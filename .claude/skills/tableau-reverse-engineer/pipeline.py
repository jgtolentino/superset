#!/usr/bin/env python3
"""
Tableau to Superset/Odoo Pipeline Orchestrator

Main pipeline that chains all skills to convert Tableau workbooks
into Superset dashboards with Odoo integration.

Pipeline Stages:
  1. fetch_gallery     - Fetch Tableau Public gallery index
  2. download_workbook - Download specific workbook (.twb/.twbx)
  3. parse_semantic    - Extract semantic model from workbook
  4. map_to_odoo       - Map semantic model to Odoo models
  5. generate_superset - Generate Superset templates
  6. generate_workflow - Generate Odoo/n8n workflow automation
  7. export_bundle     - Package as importable Superset bundle

Usage:
    # Full pipeline from Tableau Public URL
    python pipeline.py --url "https://public.tableau.com/app/profile/user/viz/Workbook"

    # From local workbook file
    python pipeline.py --file ./workbook.twbx

    # With custom Odoo model config
    python pipeline.py --file ./workbook.twbx --odoo-config ./odoo_models.json

    # Dry run (no file output)
    python pipeline.py --url "..." --dry-run

Environment Variables:
    BASE_URL              - Superset instance URL
    SUPERSET_ADMIN_USER   - Superset admin username
    SUPERSET_ADMIN_PASS   - Superset admin password
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import traceback

# Import skill modules
from fetch_gallery import fetch_tableau_gallery_index
from download_workbook import download_tableau_workbook
from parse_semantic import parse_tableau_semantic_model
from map_to_odoo import map_tableau_to_odoo_models
from generate_superset import generate_superset_templates_from_semantics
from generate_workflow import generate_workflow_automation_template
from export_bundle import export_superset_bundle, generate_import_script

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pipeline State Management
# ============================================================================

class PipelineStage(Enum):
    """Pipeline execution stages."""
    FETCH_GALLERY = "fetch_gallery"
    DOWNLOAD_WORKBOOK = "download_workbook"
    PARSE_SEMANTIC = "parse_semantic"
    MAP_TO_ODOO = "map_to_odoo"
    GENERATE_SUPERSET = "generate_superset"
    GENERATE_WORKFLOW = "generate_workflow"
    EXPORT_BUNDLE = "export_bundle"


class StageStatus(Enum):
    """Status of each pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a pipeline stage."""
    stage: str
    status: str
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    output: Any = None
    error: Optional[str] = None


@dataclass
class PipelineContext:
    """
    Shared context passed through pipeline stages.
    Accumulates results from each stage.
    """
    # Input parameters
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    output_dir: str = "./output"
    odoo_config: Optional[Dict[str, Any]] = None
    dry_run: bool = False

    # Accumulated results
    gallery_data: Optional[Dict[str, Any]] = None
    workbook_path: Optional[str] = None
    semantic_model: Optional[Dict[str, Any]] = None
    odoo_mapping: Optional[Dict[str, Any]] = None
    superset_templates: Optional[Dict[str, Any]] = None
    workflow_templates: Optional[Dict[str, Any]] = None
    bundle_result: Optional[Dict[str, Any]] = None

    # Stage tracking
    stage_results: List[StageResult] = field(default_factory=list)
    current_stage: Optional[str] = None

    # Metadata
    pipeline_id: str = ""
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.pipeline_id:
            self.pipeline_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat() + "Z"

    def record_stage(self, result: StageResult):
        """Record a stage result."""
        self.stage_results.append(result)

    def get_stage_result(self, stage: str) -> Optional[StageResult]:
        """Get result for a specific stage."""
        for result in self.stage_results:
            if result.stage == stage:
                return result
        return None

    def to_summary(self) -> Dict[str, Any]:
        """Generate pipeline execution summary."""
        return {
            "pipeline_id": self.pipeline_id,
            "source": self.source_url or self.source_file,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "stages": [
                {
                    "stage": r.stage,
                    "status": r.status,
                    "duration_seconds": r.duration_seconds,
                    "error": r.error,
                }
                for r in self.stage_results
            ],
            "output_dir": self.output_dir,
            "bundle_path": self.bundle_result.get("bundle_path") if self.bundle_result else None,
        }


# ============================================================================
# Pipeline Stage Implementations
# ============================================================================

def run_stage(
    stage: PipelineStage,
    ctx: PipelineContext,
    handler: Callable[[PipelineContext], Any],
    skip_condition: Optional[Callable[[PipelineContext], bool]] = None,
) -> bool:
    """
    Run a single pipeline stage with error handling and timing.

    Args:
        stage: Pipeline stage enum
        ctx: Pipeline context
        handler: Stage handler function
        skip_condition: Optional condition to skip stage

    Returns:
        True if stage succeeded, False otherwise
    """
    stage_name = stage.value
    ctx.current_stage = stage_name

    # Check skip condition
    if skip_condition and skip_condition(ctx):
        logger.info(f"Skipping stage: {stage_name}")
        ctx.record_stage(StageResult(
            stage=stage_name,
            status=StageStatus.SKIPPED.value,
        ))
        return True

    logger.info(f"Starting stage: {stage_name}")
    start_time = datetime.utcnow()

    try:
        result = handler(ctx)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        ctx.record_stage(StageResult(
            stage=stage_name,
            status=StageStatus.COMPLETED.value,
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z",
            duration_seconds=duration,
            output=result,
        ))

        logger.info(f"Completed stage: {stage_name} ({duration:.2f}s)")
        return True

    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"{type(e).__name__}: {str(e)}"

        logger.error(f"Failed stage: {stage_name} - {error_msg}")
        logger.debug(traceback.format_exc())

        ctx.record_stage(StageResult(
            stage=stage_name,
            status=StageStatus.FAILED.value,
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z",
            duration_seconds=duration,
            error=error_msg,
        ))

        return False


def stage_fetch_gallery(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 1: Fetch Tableau Public gallery index."""
    # Extract profile from URL if provided
    if ctx.source_url and "public.tableau.com" in ctx.source_url:
        # Parse profile from URL
        # URL format: https://public.tableau.com/app/profile/USERNAME/viz/...
        parts = ctx.source_url.split("/")
        profile_idx = next((i for i, p in enumerate(parts) if p == "profile"), -1)
        if profile_idx >= 0 and profile_idx + 1 < len(parts):
            profile_name = parts[profile_idx + 1]
            result = fetch_tableau_gallery_index(
                profile_name=profile_name,
                output_dir=ctx.output_dir,
            )
            ctx.gallery_data = result
            return result

    # If no profile, fetch featured gallery
    result = fetch_tableau_gallery_index(
        output_dir=ctx.output_dir,
        max_workbooks=10,
    )
    ctx.gallery_data = result
    return result


def stage_download_workbook(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 2: Download Tableau workbook."""
    if ctx.source_file:
        # Use provided file
        ctx.workbook_path = ctx.source_file
        return {"status": "skipped", "path": ctx.source_file, "message": "Using provided file"}

    if not ctx.source_url:
        raise ValueError("No source URL or file provided")

    result = download_tableau_workbook(
        workbook_url=ctx.source_url,
        output_dir=ctx.output_dir,
    )

    if result.get("status") == "success":
        ctx.workbook_path = result.get("path")

    return result


def stage_parse_semantic(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 3: Parse semantic model from workbook."""
    if not ctx.workbook_path:
        raise ValueError("No workbook path available")

    result = parse_tableau_semantic_model(
        workbook_path=ctx.workbook_path,
        output_dir=ctx.output_dir,
    )

    if result.get("status") == "success":
        ctx.semantic_model = result.get("semantic_model")

    return result


def stage_map_to_odoo(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 4: Map semantic model to Odoo models."""
    if not ctx.semantic_model:
        raise ValueError("No semantic model available")

    result = map_tableau_to_odoo_models(
        semantic_model=ctx.semantic_model,
        odoo_config=ctx.odoo_config,
        output_dir=ctx.output_dir,
    )

    if result.get("status") == "success":
        ctx.odoo_mapping = result.get("mapping")

    return result


def stage_generate_superset(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 5: Generate Superset templates."""
    if not ctx.semantic_model:
        raise ValueError("No semantic model available")

    result = generate_superset_templates_from_semantics(
        semantic_model=ctx.semantic_model,
        odoo_mapping=ctx.odoo_mapping,
        output_dir=ctx.output_dir,
    )

    if result.get("status") == "success":
        ctx.superset_templates = result.get("templates")

    return result


def stage_generate_workflow(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 6: Generate workflow automation templates."""
    if not ctx.semantic_model:
        raise ValueError("No semantic model available")

    result = generate_workflow_automation_template(
        semantic_model=ctx.semantic_model,
        odoo_mapping=ctx.odoo_mapping,
        superset_templates=ctx.superset_templates,
        output_dir=ctx.output_dir,
    )

    if result.get("status") == "success":
        ctx.workflow_templates = result.get("templates")

    return result


def stage_export_bundle(ctx: PipelineContext) -> Dict[str, Any]:
    """Stage 7: Export Superset bundle."""
    if not ctx.superset_templates:
        raise ValueError("No Superset templates available")

    if ctx.dry_run:
        return {"status": "skipped", "message": "Dry run - no bundle exported"}

    # Derive bundle name from source
    bundle_name = None
    if ctx.source_file:
        bundle_name = Path(ctx.source_file).stem
    elif ctx.source_url:
        # Extract workbook name from URL
        parts = ctx.source_url.rstrip("/").split("/")
        if "viz" in parts:
            viz_idx = parts.index("viz")
            if viz_idx + 1 < len(parts):
                bundle_name = parts[viz_idx + 1]

    result = export_superset_bundle(
        superset_templates=ctx.superset_templates,
        output_dir=os.path.join(ctx.output_dir, "bundles"),
        bundle_name=bundle_name,
        format="zip",
    )

    ctx.bundle_result = result

    # Generate import script
    if result.get("status") == "success" and result.get("bundle_path"):
        script_path = Path(ctx.output_dir) / "bundles" / f"import_{result.get('bundle_name', 'bundle')}.sh"
        script_content = generate_import_script(result["bundle_path"])
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        result["import_script"] = str(script_path)

    return result


# ============================================================================
# Main Pipeline Orchestrator
# ============================================================================

class TableauToSupersetPipeline:
    """
    Main pipeline orchestrator for Tableau to Superset/Odoo conversion.
    """

    def __init__(
        self,
        source_url: Optional[str] = None,
        source_file: Optional[str] = None,
        output_dir: str = "./output",
        odoo_config: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ):
        self.ctx = PipelineContext(
            source_url=source_url,
            source_file=source_file,
            output_dir=output_dir,
            odoo_config=odoo_config,
            dry_run=dry_run,
        )

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def run(
        self,
        start_stage: Optional[PipelineStage] = None,
        end_stage: Optional[PipelineStage] = None,
        skip_stages: Optional[List[PipelineStage]] = None,
    ) -> PipelineContext:
        """
        Run the pipeline.

        Args:
            start_stage: Stage to start from (default: FETCH_GALLERY)
            end_stage: Stage to stop at (default: EXPORT_BUNDLE)
            skip_stages: List of stages to skip

        Returns:
            Pipeline context with all results
        """
        skip_stages = skip_stages or []

        # Define stage order
        stages = [
            (PipelineStage.FETCH_GALLERY, stage_fetch_gallery),
            (PipelineStage.DOWNLOAD_WORKBOOK, stage_download_workbook),
            (PipelineStage.PARSE_SEMANTIC, stage_parse_semantic),
            (PipelineStage.MAP_TO_ODOO, stage_map_to_odoo),
            (PipelineStage.GENERATE_SUPERSET, stage_generate_superset),
            (PipelineStage.GENERATE_WORKFLOW, stage_generate_workflow),
            (PipelineStage.EXPORT_BUNDLE, stage_export_bundle),
        ]

        # Find start/end indices
        stage_list = [s[0] for s in stages]
        start_idx = 0 if not start_stage else stage_list.index(start_stage)
        end_idx = len(stages) - 1 if not end_stage else stage_list.index(end_stage)

        # Adjust stages if we have a local file
        if self.ctx.source_file:
            # Skip gallery fetch if we have a file
            if PipelineStage.FETCH_GALLERY not in skip_stages:
                skip_stages.append(PipelineStage.FETCH_GALLERY)

        logger.info(f"Starting pipeline {self.ctx.pipeline_id}")
        logger.info(f"Source: {self.ctx.source_url or self.ctx.source_file}")
        logger.info(f"Output: {self.ctx.output_dir}")

        # Run stages
        for i, (stage, handler) in enumerate(stages):
            if i < start_idx or i > end_idx:
                continue

            def should_skip(ctx, skip_list=skip_stages, st=stage):
                return st in skip_list

            success = run_stage(
                stage=stage,
                ctx=self.ctx,
                handler=handler,
                skip_condition=lambda ctx, sl=skip_stages, s=stage: s in sl,
            )

            if not success:
                logger.error(f"Pipeline failed at stage: {stage.value}")
                break

        # Mark completion
        self.ctx.completed_at = datetime.utcnow().isoformat() + "Z"

        # Save pipeline summary
        if not self.ctx.dry_run:
            summary_path = Path(self.ctx.output_dir) / f"pipeline_summary_{self.ctx.pipeline_id}.json"
            with open(summary_path, 'w') as f:
                json.dump(self.ctx.to_summary(), f, indent=2)
            logger.info(f"Pipeline summary saved: {summary_path}")

        return self.ctx

    def run_from_file(self, file_path: str) -> PipelineContext:
        """
        Run pipeline from a local workbook file.
        Skips download stage.
        """
        self.ctx.source_file = file_path
        return self.run(
            start_stage=PipelineStage.PARSE_SEMANTIC,
            skip_stages=[PipelineStage.FETCH_GALLERY, PipelineStage.DOWNLOAD_WORKBOOK],
        )

    def run_semantic_only(self) -> PipelineContext:
        """
        Run only semantic parsing stages (no Superset/workflow generation).
        """
        return self.run(end_stage=PipelineStage.MAP_TO_ODOO)


def run_pipeline(
    source_url: Optional[str] = None,
    source_file: Optional[str] = None,
    output_dir: str = "./output",
    odoo_config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to run the full pipeline.

    Args:
        source_url: Tableau Public workbook URL
        source_file: Local workbook file path
        output_dir: Output directory
        odoo_config: Custom Odoo model configuration
        dry_run: If True, don't write output files

    Returns:
        Pipeline execution summary
    """
    pipeline = TableauToSupersetPipeline(
        source_url=source_url,
        source_file=source_file,
        output_dir=output_dir,
        odoo_config=odoo_config,
        dry_run=dry_run,
    )

    ctx = pipeline.run()
    return ctx.to_summary()


# ============================================================================
# Batch Processing
# ============================================================================

def run_batch_pipeline(
    workbook_list: List[Dict[str, str]],
    output_dir: str = "./output",
    odoo_config: Optional[Dict[str, Any]] = None,
    continue_on_error: bool = True,
) -> List[Dict[str, Any]]:
    """
    Run pipeline on multiple workbooks.

    Args:
        workbook_list: List of dicts with 'url' or 'file' keys
        output_dir: Base output directory
        odoo_config: Shared Odoo configuration
        continue_on_error: Continue processing if one workbook fails

    Returns:
        List of pipeline summaries
    """
    results = []

    for i, workbook in enumerate(workbook_list):
        logger.info(f"Processing workbook {i+1}/{len(workbook_list)}")

        # Create workbook-specific output dir
        workbook_name = workbook.get("name", f"workbook_{i+1}")
        workbook_output = os.path.join(output_dir, workbook_name)

        try:
            summary = run_pipeline(
                source_url=workbook.get("url"),
                source_file=workbook.get("file"),
                output_dir=workbook_output,
                odoo_config=odoo_config,
            )
            results.append(summary)

        except Exception as e:
            logger.error(f"Failed to process workbook: {workbook} - {e}")
            if not continue_on_error:
                raise
            results.append({
                "source": workbook.get("url") or workbook.get("file"),
                "status": "failed",
                "error": str(e),
            })

    return results


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Tableau to Superset/Odoo Conversion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert from Tableau Public URL
  python pipeline.py --url "https://public.tableau.com/app/profile/user/viz/SalesDashboard"

  # Convert from local file
  python pipeline.py --file ./workbook.twbx

  # With custom output directory
  python pipeline.py --file ./workbook.twbx --output ./converted

  # Batch processing
  python pipeline.py --batch ./workbooks.json

  # Dry run (no file output)
  python pipeline.py --url "..." --dry-run
        """
    )

    # Input sources
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url", "-u",
        help="Tableau Public workbook URL"
    )
    input_group.add_argument(
        "--file", "-f",
        help="Local workbook file path (.twb or .twbx)"
    )
    input_group.add_argument(
        "--batch", "-b",
        help="JSON file with list of workbooks to process"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--odoo-config",
        help="JSON file with custom Odoo model configuration"
    )

    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing output files"
    )
    parser.add_argument(
        "--start-stage",
        choices=[s.value for s in PipelineStage],
        help="Stage to start from"
    )
    parser.add_argument(
        "--end-stage",
        choices=[s.value for s in PipelineStage],
        help="Stage to stop at"
    )
    parser.add_argument(
        "--skip-stages",
        nargs="+",
        choices=[s.value for s in PipelineStage],
        help="Stages to skip"
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load Odoo config if provided
    odoo_config = None
    if args.odoo_config:
        with open(args.odoo_config) as f:
            odoo_config = json.load(f)

    # Run pipeline
    try:
        if args.batch:
            # Batch processing
            with open(args.batch) as f:
                workbook_list = json.load(f)

            results = run_batch_pipeline(
                workbook_list=workbook_list,
                output_dir=args.output,
                odoo_config=odoo_config,
            )

            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(f"\nProcessed {len(results)} workbooks")
                for r in results:
                    status = "OK" if r.get("completed_at") else "FAILED"
                    print(f"  - {r.get('source', 'unknown')}: {status}")

        else:
            # Single workbook
            pipeline = TableauToSupersetPipeline(
                source_url=args.url,
                source_file=args.file,
                output_dir=args.output,
                odoo_config=odoo_config,
                dry_run=args.dry_run,
            )

            # Parse stage options
            start_stage = PipelineStage(args.start_stage) if args.start_stage else None
            end_stage = PipelineStage(args.end_stage) if args.end_stage else None
            skip_stages = [PipelineStage(s) for s in (args.skip_stages or [])]

            ctx = pipeline.run(
                start_stage=start_stage,
                end_stage=end_stage,
                skip_stages=skip_stages,
            )

            summary = ctx.to_summary()

            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print(f"\nPipeline {summary['pipeline_id']} completed")
                print(f"Source: {summary['source']}")
                print(f"Output: {summary['output_dir']}")
                print("\nStages:")
                for stage in summary["stages"]:
                    status_icon = {
                        "completed": "[OK]",
                        "failed": "[FAIL]",
                        "skipped": "[SKIP]",
                    }.get(stage["status"], "[?]")
                    print(f"  {status_icon} {stage['stage']} ({stage['duration_seconds']:.2f}s)")
                    if stage.get("error"):
                        print(f"      Error: {stage['error']}")

                if summary.get("bundle_path"):
                    print(f"\nBundle: {summary['bundle_path']}")
                    print(f"Import: superset import-dashboards -p {summary['bundle_path']}")

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
