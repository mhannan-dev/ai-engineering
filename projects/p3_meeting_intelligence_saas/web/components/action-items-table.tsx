'use client';

import React, { useState } from 'react';
import {
  CheckSquare,
  Square,
  Clock,
  User,
  Calendar,
  Search,
  Filter,
  ArrowUpDown,
  Download,
} from 'lucide-react';
import { ActionItem, Priority, ActionItemStatus } from '@/lib/api';

interface ActionItemsTableProps {
  initialItems: ActionItem[];
}

export function ActionItemsTable({ initialItems }: ActionItemsTableProps) {
  const [items, setItems] = useState<ActionItem[]>(initialItems);
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const toggleStatus = (id: string) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const nextStatus: ActionItemStatus =
            item.status === 'completed'
              ? 'pending'
              : item.status === 'pending'
              ? 'in_progress'
              : 'completed';
          return { ...item, status: nextStatus };
        }
        return item;
      })
    );
  };

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.task.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.assignee.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPriority = priorityFilter === 'all' || item.priority === priorityFilter;
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesPriority && matchesStatus;
  });

  const exportCSV = () => {
    const header = 'Task,Assignee,Due Date,Priority,Status\n';
    const rows = filteredItems
      .map(
        (i) =>
          `"${i.task.replace(/"/g, '""')}","${i.assignee}","${i.due_date}","${i.priority}","${i.status}"`
      )
      .join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `meeting_action_items_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      {/* Title & Controls */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            Action Items & Deliverables
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Synthesized and validated through Pydantic v2 schema. Click checkbox to advance status.
          </p>
        </div>

        <button
          onClick={exportCSV}
          className="btn-secondary"
          style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
        >
          <Download size={15} />
          Export CSV
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '1.5rem',
        }}
      >
        {/* Search */}
        <div
          style={{
            position: 'relative',
            flex: '1 1 240px',
            minWidth: '200px',
          }}
        >
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            type="text"
            placeholder="Search action items or assignees..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.6rem 0.75rem 0.6rem 2.25rem',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontSize: '0.88rem',
              outline: 'none',
            }}
          />
        </div>

        {/* Priority Filter */}
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          style={{
            padding: '0.6rem 0.85rem',
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          <option value="all">All Priorities</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: '0.6rem 0.85rem',
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Table Container */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr
              style={{
                borderBottom: '1px solid var(--border-subtle)',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <th style={{ padding: '0.75rem 0.5rem', width: '40px' }}>Done</th>
              <th style={{ padding: '0.75rem 1rem' }}>Task Description</th>
              <th style={{ padding: '0.75rem 1rem' }}>Assignee</th>
              <th style={{ padding: '0.75rem 1rem' }}>Due Date</th>
              <th style={{ padding: '0.75rem 1rem' }}>Priority</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                  No action items match the current filters.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => {
                const isDone = item.status === 'completed';
                return (
                  <tr
                    key={item.id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      backgroundColor: isDone ? 'rgba(255, 255, 255, 0.01)' : 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '0.85rem 0.5rem', verticalAlign: 'middle' }}>
                      <button
                        onClick={() => toggleStatus(item.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: isDone ? 'var(--accent-emerald)' : 'var(--text-muted)',
                          display: 'flex',
                          alignItems: 'center',
                          padding: '0.2rem',
                        }}
                        title={`Current: ${item.status}. Click to cycle.`}
                      >
                        {isDone ? <CheckSquare size={18} /> : <Square size={18} />}
                      </button>
                    </td>

                    <td
                      style={{
                        padding: '0.85rem 1rem',
                        color: isDone ? 'var(--text-muted)' : 'var(--text-primary)',
                        textDecoration: isDone ? 'line-through' : 'none',
                        fontSize: '0.92rem',
                        fontWeight: isDone ? 400 : 500,
                      }}
                    >
                      {item.task}
                    </td>

                    <td style={{ padding: '0.85rem 1rem', whiteSpace: 'nowrap' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          fontSize: '0.85rem',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        <User size={13} style={{ color: 'var(--accent-cyan)' }} />
                        {item.assignee}
                      </span>
                    </td>

                    <td style={{ padding: '0.85rem 1rem', whiteSpace: 'nowrap' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          fontSize: '0.82rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        <Calendar size={13} />
                        {item.due_date}
                      </span>
                    </td>

                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span className={`badge badge-${item.priority}`}>
                        {item.priority}
                      </span>
                    </td>

                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span
                        onClick={() => toggleStatus(item.id)}
                        style={{
                          cursor: 'pointer',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          padding: '0.2rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          background:
                            item.status === 'completed'
                              ? 'rgba(16, 185, 129, 0.15)'
                              : item.status === 'in_progress'
                              ? 'rgba(59, 130, 246, 0.15)'
                              : 'rgba(255, 255, 255, 0.05)',
                          color:
                            item.status === 'completed'
                              ? 'var(--accent-emerald)'
                              : item.status === 'in_progress'
                              ? '#60a5fa'
                              : 'var(--text-muted)',
                          border: `1px solid ${
                            item.status === 'completed'
                              ? 'rgba(16, 185, 129, 0.3)'
                              : item.status === 'in_progress'
                              ? 'rgba(59, 130, 246, 0.3)'
                              : 'var(--border-subtle)'
                          }`,
                        }}
                      >
                        {item.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
