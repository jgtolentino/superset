import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const CreateActionSchema = z.object({
  project_id: z.string().optional(),
  title: z.string().min(1).max(500),
  description: z.string().max(5000).optional(),
  assignee: z.string().optional(),
  due_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  source: z.enum(['advisor', 'dq', 'manual']),
  source_id: z.string().optional(),
  priority: z.enum(['high', 'medium', 'low']).optional(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = CreateActionSchema.parse(body);

    const notionApiKey = process.env.NOTION_API_KEY;
    const actionsDbId = process.env.NOTION_ACTIONS_DB_ID;

    if (!notionApiKey || !actionsDbId) {
      return NextResponse.json(
        { error: { code: 'CONFIGURATION_ERROR', message: 'Notion not configured' } },
        { status: 500 }
      );
    }

    // Create page in Notion
    const response = await fetch('https://api.notion.com/v1/pages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${notionApiKey}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        parent: { database_id: actionsDbId },
        properties: {
          Title: {
            title: [{ text: { content: data.title } }],
          },
          Status: {
            select: { name: 'todo' },
          },
          Source: {
            select: { name: data.source },
          },
          Priority: data.priority
            ? { select: { name: data.priority } }
            : undefined,
          'Due Date': data.due_date
            ? { date: { start: data.due_date } }
            : undefined,
          Description: data.description
            ? { rich_text: [{ text: { content: data.description } }] }
            : undefined,
          'Source ID': data.source_id
            ? { rich_text: [{ text: { content: data.source_id } }] }
            : undefined,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Notion API error:', error);
      return NextResponse.json(
        { error: { code: 'NOTION_ERROR', message: 'Failed to create action' } },
        { status: 500 }
      );
    }

    const result = await response.json();

    return NextResponse.json({
      success: true,
      action_id: result.id,
      notion_url: result.url,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', details: error.errors } },
        { status: 400 }
      );
    }

    console.error('Failed to create action:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to create action' } },
      { status: 500 }
    );
  }
}
