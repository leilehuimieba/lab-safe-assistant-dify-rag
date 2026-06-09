import { startTransition, useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties, UIEvent } from 'react';
import * as echarts from 'echarts/core';
import { ScatterChart, SunburstChart } from 'echarts/charts';
import { TooltipComponent, TitleComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { jsonFetch } from '../hooks/useApi';

echarts.use([ScatterChart, SunburstChart, TooltipComponent, TitleComponent, GridComponent, CanvasRenderer]);

interface Subcategory {
  name: string;
  count: number;
  called_count: number;
  coverage_rate: number;
}

interface Category {
  name: string;
  count: number;
  called_count: number;
  coverage_rate: number;
  subcategories: Subcategory[];
}

interface KBSummary {
  total_entries: number;
  total_categories: number;
  called_entries: number;
  coverage_rate: number;
  categories: Category[];
}

interface KBEntry {
  id: string;
  title: string;
  category: string;
  subcategory: string;
  risk_level: string;
  called: boolean;
  call_count: number;
  source_title: string;
  source_org: string;
  source_url: string;
  question: string;
  answer: string;
}

interface KBEntriesResponse {
  total: number;
  offset: number;
  limit: number;
  has_more: boolean;
  next_offset: number | null;
  entries: KBEntry[];
}

type SortBy = 'call_count' | 'title' | 'risk_level';
type SortOrder = 'asc' | 'desc';

const PAGE_SIZE = 120;
const ROW_HEIGHT = 92;
const ROW_OVERSCAN = 4;

const COLORS = {
  bg: '#07111f',
  card: '#132337',
  panel: '#0b1728',
  text: '#f1f5f9',
  text2: '#94a3b8',
  cyan: '#06b6d4',
  blue: '#38bdf8',
  emerald: '#10b981',
  amber: '#f59e0b',
  red: '#ef4444',
  violet: '#a3e635',
  glow: 'rgba(6, 182, 212, 0.28)',
};

function useKBSummary() {
  const [data, setData] = useState<KBSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    jsonFetch<KBSummary>('/api/kb/summary')
      .then((payload) => {
        setData(payload);
        setLoading(false);
      })
      .catch((reason) => {
        setError(reason instanceof Error ? reason.message : String(reason));
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}

async function fetchKBEntriesPage(params: {
  category: string;
  subcategory: string;
  keyword: string;
  sortBy: SortBy;
  sortOrder: SortOrder;
  offset: number;
  limit: number;
}): Promise<KBEntriesResponse> {
  const search = new URLSearchParams();
  search.set('category', params.category);
  if (params.subcategory) {
    search.set('subcategory', params.subcategory);
  }
  if (params.keyword) {
    search.set('keyword', params.keyword);
  }
  search.set('sort_by', params.sortBy);
  search.set('sort_order', params.sortOrder);
  search.set('offset', String(params.offset));
  search.set('limit', String(params.limit));
  return jsonFetch<KBEntriesResponse>(`/api/kb/entries?${search.toString()}`);
}

function mergeEntries(current: KBEntry[], incoming: KBEntry[]): KBEntry[] {
  if (!current.length) {
    return incoming;
  }
  const seen = new Set(current.map((entry) => entry.id));
  const merged = [...current];
  for (const entry of incoming) {
    if (!seen.has(entry.id)) {
      seen.add(entry.id);
      merged.push(entry);
    }
  }
  return merged;
}

function useKBEntries(category: string, subcategory: string, keyword: string, sortBy: SortBy, sortOrder: SortOrder) {
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    const requestId = requestIdRef.current;

    if (!category) {
      setEntries([]);
      setTotal(0);
      setHasMore(false);
      setError('');
      setLoading(false);
      setLoadingMore(false);
      return;
    }

    setEntries([]);
    setTotal(0);
    setHasMore(false);
    setError('');
    setLoading(true);
    setLoadingMore(false);

    void fetchKBEntriesPage({
      category,
      subcategory,
      keyword,
      sortBy,
      sortOrder,
      offset: 0,
      limit: PAGE_SIZE,
    }).then((payload) => {
      if (requestIdRef.current !== requestId) {
        return;
      }
      setEntries(payload.entries || []);
      setTotal(payload.total || 0);
      setHasMore(Boolean(payload.has_more));
    }).catch((reason) => {
      if (requestIdRef.current !== requestId) {
        return;
      }
      setError(reason instanceof Error ? reason.message : '知识条目加载失败');
    }).finally(() => {
      if (requestIdRef.current === requestId) {
        setLoading(false);
      }
    });
  }, [category, subcategory, keyword, sortBy, sortOrder]);

  const loadMore = useCallback(async () => {
    if (!category || loading || loadingMore || !hasMore) {
      return;
    }
    const requestId = requestIdRef.current;
    setLoadingMore(true);
    try {
      const payload = await fetchKBEntriesPage({
        category,
        subcategory,
        keyword,
        sortBy,
        sortOrder,
        offset: entries.length,
        limit: PAGE_SIZE,
      });
      if (requestIdRef.current !== requestId) {
        return;
      }
      setEntries((current) => mergeEntries(current, payload.entries || []));
      setTotal(payload.total || 0);
      setHasMore(Boolean(payload.has_more));
    } catch (reason) {
      if (requestIdRef.current !== requestId) {
        return;
      }
      setError(reason instanceof Error ? reason.message : '知识条目加载失败');
    } finally {
      if (requestIdRef.current === requestId) {
        setLoadingMore(false);
      }
    }
  }, [category, entries.length, hasMore, keyword, loading, loadingMore, sortBy, sortOrder, subcategory]);

  return { entries, total, loading, loadingMore, hasMore, error, loadMore };
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div
      className="kbv-stat-card"
      style={{
        minWidth: 150,
        '--accent': color || COLORS.cyan,
      } as CSSProperties}
    >
      <div className="kbv-stat-label">{label}</div>
      <div className="kbv-stat-value" style={{ color: color || COLORS.cyan }}>{value}</div>
    </div>
  );
}

function ToolbarLabel({ text }: { text: string }) {
  return <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 6 }}>{text}</div>;
}

export default function KBVisualization() {
  const { data, loading, error } = useKBSummary();
  const [level, setLevel] = useState<'l1' | 'l2' | 'l3'>('l1');
  const [selCat, setSelCat] = useState('');
  const [selSub, setSelSub] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerEntry, setDrawerEntry] = useState<KBEntry | null>(null);
  const [keywordInput, setKeywordInput] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('call_count');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const deferredKeyword = useDeferredValue(keywordInput.trim());

  const bubbleRef = useRef<HTMLDivElement>(null);
  const sunburstRef = useRef<HTMLDivElement>(null);
  const listViewportRef = useRef<HTMLDivElement>(null);
  const bubbleChart = useRef<echarts.ECharts | null>(null);
  const sunburstChart = useRef<echarts.ECharts | null>(null);
  const [listHeight, setListHeight] = useState(480);
  const [scrollTop, setScrollTop] = useState(0);

  useEffect(() => {
    if (level !== 'l3') {
      setKeywordInput('');
      setSortBy('call_count');
      setSortOrder('desc');
      setScrollTop(0);
    }
  }, [level, selCat, selSub]);

  const syncListHeight = useCallback(() => {
    const nextHeight = listViewportRef.current?.clientHeight ?? Math.max(window.innerHeight - 340, 360);
    setListHeight(nextHeight);
  }, []);

  useEffect(() => {
    syncListHeight();
    window.addEventListener('resize', syncListHeight);
    return () => window.removeEventListener('resize', syncListHeight);
  }, [syncListHeight]);

  // L1 Bubble Chart
  useEffect(() => {
    if (!data || level !== 'l1' || !bubbleRef.current) {
      return;
    }
    if (bubbleChart.current) {
      bubbleChart.current.dispose();
    }
    const chart = echarts.init(bubbleRef.current, undefined, { renderer: 'canvas' });
    bubbleChart.current = chart;

    const categories = data.categories;
    const maxCount = Math.max(...categories.map((item) => item.count), 1);
    const seriesData = categories.map((item, index) => ({
      name: item.name,
      value: [index, item.count, item.count, item.coverage_rate],
      itemStyle: {
        color: item.coverage_rate > 0
          ? `rgba(16, 185, 129, ${0.4 + item.coverage_rate / 200})`
          : 'rgba(239, 68, 68, 0.5)',
        borderColor: item.coverage_rate > 0 ? COLORS.emerald : COLORS.red,
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: item.coverage_rate > 0 ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
      },
    }));

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '知识库分类全景', left: 'center', textStyle: { color: COLORS.text, fontSize: 18 } },
      tooltip: {
        backgroundColor: COLORS.card,
        borderColor: COLORS.cyan,
        textStyle: { color: COLORS.text },
        formatter: (params: { dataIndex: number }) => {
          const category = categories[params.dataIndex];
          return `<b>${category.name}</b><br/>条目数: ${category.count}<br/>已调用: ${category.called_count}<br/>覆盖率: ${category.coverage_rate}%`;
        },
      },
      grid: { left: 40, right: 40, top: 60, bottom: 40 },
      xAxis: {
        type: 'category',
        data: categories.map((item) => item.name),
        axisLabel: { color: COLORS.text2, rotate: 45, interval: 0, fontSize: 10 },
        axisLine: { lineStyle: { color: COLORS.text2 } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '条目数',
        nameTextStyle: { color: COLORS.text2 },
        axisLabel: { color: COLORS.text2 },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } },
      },
      series: [{
        type: 'scatter',
        symbolSize: (value: number[]) => Math.max(20, (value[2] / maxCount) * 80),
        data: seriesData,
        emphasis: {
          itemStyle: { shadowBlur: 20, shadowColor: COLORS.cyan },
        },
      }],
    });

    chart.on('click', (params: { dataIndex: number }) => {
      const category = categories[params.dataIndex];
      if (!category) {
        return;
      }
      startTransition(() => {
        setSelCat(category.name);
        setSelSub('');
        setLevel('l2');
      });
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, [data, level]);

  // L2 Sunburst
  const catData = useMemo(() => data?.categories.find((item) => item.name === selCat), [data, selCat]);

  useEffect(() => {
    if (!catData || level !== 'l2' || !sunburstRef.current) {
      return;
    }
    if (sunburstChart.current) {
      sunburstChart.current.dispose();
    }
    const chart = echarts.init(sunburstRef.current, undefined, { renderer: 'canvas' });
    sunburstChart.current = chart;

    const sunData = catData.subcategories.map((sub) => ({
      name: sub.name,
      value: sub.count,
      itemStyle: {
        color: sub.coverage_rate > 0
          ? `rgba(16, 185, 129, ${0.3 + sub.coverage_rate / 150})`
          : 'rgba(239, 68, 68, 0.4)',
      },
      children: [],
    }));

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: `${selCat} - 子分类分布`, left: 'center', textStyle: { color: COLORS.text, fontSize: 18 } },
      tooltip: {
        backgroundColor: COLORS.card,
        borderColor: COLORS.cyan,
        textStyle: { color: COLORS.text },
        formatter: (params: { name: string }) => {
          const sub = catData.subcategories.find((item) => item.name === params.name);
          if (!sub) {
            return params.name;
          }
          return `<b>${sub.name}</b><br/>条目数: ${sub.count}<br/>已调用: ${sub.called_count}<br/>覆盖率: ${sub.coverage_rate}%`;
        },
      },
      series: [{
        type: 'sunburst',
        data: sunData,
        radius: [40, '80%'],
        itemStyle: { borderRadius: 6, borderWidth: 1, borderColor: COLORS.bg },
        label: { color: COLORS.text, fontSize: 11 },
        emphasis: { itemStyle: { shadowBlur: 15, shadowColor: COLORS.cyan } },
      }],
    });

    chart.on('click', (params: { name: string }) => {
      startTransition(() => {
        setSelSub(params.name);
        setLevel('l3');
      });
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, [catData, level, selCat]);

  const { entries: l3Entries, total: l3Total, loading: l3Loading, loadingMore, hasMore, error: l3Error, loadMore } = useKBEntries(
    selCat,
    selSub,
    deferredKeyword,
    sortBy,
    sortOrder,
  );

  useEffect(() => {
    if (level !== 'l3' || !listViewportRef.current) {
      return;
    }
    listViewportRef.current.scrollTop = 0;
    setScrollTop(0);
    syncListHeight();
  }, [level, selCat, selSub, deferredKeyword, sortBy, sortOrder, syncListHeight]);

  useEffect(() => {
    if (level !== 'l3' || !hasMore || loadingMore || l3Loading || !listViewportRef.current) {
      return;
    }
    const viewport = listViewportRef.current;
    if (viewport.scrollHeight <= viewport.clientHeight + ROW_HEIGHT * 2) {
      void loadMore();
    }
  }, [hasMore, l3Entries.length, l3Loading, level, loadMore, loadingMore]);

  const openDrawer = useCallback((entry: KBEntry) => {
    setDrawerEntry(entry);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawerOpen(false);
    setDrawerEntry(null);
  }, []);

  useEffect(() => {
    if (!drawerOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeDrawer();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [closeDrawer, drawerOpen]);

  const handleBack = useCallback(() => {
    startTransition(() => {
      if (level === 'l3') {
        setLevel('l2');
        setSelSub('');
        return;
      }
      setLevel('l1');
      setSelCat('');
      setSelSub('');
    });
  }, [level]);

  const handleListScroll = useCallback((event: UIEvent<HTMLDivElement>) => {
    const viewport = event.currentTarget;
    setScrollTop(viewport.scrollTop);
    const remaining = viewport.scrollHeight - (viewport.scrollTop + viewport.clientHeight);
    if (remaining < ROW_HEIGHT * 4 && hasMore && !loadingMore && !l3Loading) {
      void loadMore();
    }
  }, [hasMore, l3Loading, loadMore, loadingMore]);

  const visibleCount = Math.max(1, Math.ceil(listHeight / ROW_HEIGHT));
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - ROW_OVERSCAN);
  const endIndex = Math.min(l3Entries.length, startIndex + visibleCount + ROW_OVERSCAN * 2);
  const visibleEntries = l3Entries.slice(startIndex, endIndex);
  const totalHeight = l3Entries.length * ROW_HEIGHT;
  const hotCategories = useMemo(() => {
    return [...(data?.categories || [])].sort((a, b) => b.count - a.count).slice(0, 6);
  }, [data]);
  const hotSubcategories = useMemo(() => {
    return [...(catData?.subcategories || [])].sort((a, b) => b.count - a.count).slice(0, 8);
  }, [catData]);
  const loadedRate = l3Total > 0 ? Math.min(100, Math.round((l3Entries.length / l3Total) * 100)) : 0;

  const renderRow = useCallback((entry: KBEntry, index: number) => {
    const style: CSSProperties = {
      position: 'absolute',
      top: index * ROW_HEIGHT,
      left: 0,
      right: 0,
      height: ROW_HEIGHT,
      padding: '0 12px',
    };
    return (
      <div key={`${entry.id}-${index}`} style={style}>
        <div
          onClick={() => openDrawer(entry)}
          style={{
            background: COLORS.card,
            borderRadius: 8,
            padding: '12px 16px',
            border: `1px solid ${entry.called ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            height: ROW_HEIGHT - 12,
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: entry.called ? COLORS.emerald : COLORS.red,
              boxShadow: `0 0 8px ${entry.called ? COLORS.emerald : COLORS.red}`,
              flexShrink: 0,
            }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: COLORS.text, fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {entry.title || entry.id}
            </div>
            <div style={{ color: COLORS.text2, fontSize: 12, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {entry.category} · {entry.subcategory} · 风险等级: {entry.risk_level || 'N/A'}
            </div>
            <div style={{ color: COLORS.text2, fontSize: 11, marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              来源: {entry.source_org || entry.source_title || '未标注'}
            </div>
          </div>
          <div style={{ color: entry.called ? COLORS.emerald : COLORS.red, fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
            {entry.called ? `已调用 ${entry.call_count || 0}` : '未调用'}
          </div>
        </div>
      </div>
    );
  }, [openDrawer]);

  if (loading) {
    return (
      <div className="kbv-shell kbv-center">
        <div style={{ textAlign: 'center' }}>
          <div className="kbv-loader-orb" />
          <div style={{ fontSize: 28, marginBottom: 12 }}>正在加载知识库态势舱...</div>
          <div className="kbv-loading-track">
            <div className="kbv-loading-fill" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: COLORS.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: COLORS.red }}>
        <div>加载失败: {error || '无数据'}</div>
      </div>
    );
  }

  return (
    <div className="kbv-shell">
      <div className="kbv-orb kbv-orb-a" />
      <div className="kbv-orb kbv-orb-b" />
      <div className="kbv-scanline" />

      <div className="kbv-topbar">
        <a href="#/" className="kbv-back-link">← 返回对话</a>
        <div className="kbv-divider" />
        <div>
          <div className="kbv-title">知识库态势感知舱</div>
          <div className="kbv-subtitle">3000+ 条实验室安全知识 · 分页加载 · 虚拟渲染</div>
        </div>
        <div style={{ flex: 1 }} />
        {level !== 'l1' && (
          <button
            onClick={handleBack}
            className="kbv-ghost-btn"
          >
            ← 返回上级
          </button>
        )}
        <div className="kbv-route-pill">
          {level === 'l1' ? '全景视图' : level === 'l2' ? selCat : `${selCat} > ${selSub}`}
        </div>
      </div>

      <div className="kbv-stat-row">
        <StatCard label="总条目" value={data.total_entries} />
        <StatCard label="分类数" value={data.total_categories} />
        <StatCard label="已调用" value={data.called_entries} color={COLORS.emerald} />
        <StatCard label="未调用" value={data.total_entries - data.called_entries} color={COLORS.red} />
        <StatCard label="覆盖率" value={`${data.coverage_rate}%`} color={COLORS.cyan} />
      </div>

      <div className="kbv-main">
        {level === 'l1' && (
          <div className="kbv-stage kbv-stage-with-side">
            <div className="kbv-chart-card">
              <div ref={bubbleRef} style={{ width: '100%', height: '100%' }} />
            </div>
            <aside className="kbv-side-panel">
              <div className="kbv-panel-kicker">TOP SIGNALS</div>
              <h3>高密度知识域</h3>
              <p>只渲染前 6 个摘要信号，主图仍由 Canvas 承载。</p>
              <div className="kbv-signal-list">
                {hotCategories.map((category, index) => (
                  <button
                    key={category.name}
                    className="kbv-signal"
                    onClick={() => {
                      startTransition(() => {
                        setSelCat(category.name);
                        setSelSub('');
                        setLevel('l2');
                      });
                    }}
                  >
                    <span className="kbv-signal-rank">{String(index + 1).padStart(2, '0')}</span>
                    <span className="kbv-signal-body">
                      <strong>{category.name}</strong>
                      <span>{category.count} 条 · 覆盖 {category.coverage_rate}%</span>
                    </span>
                  </button>
                ))}
              </div>
            </aside>
          </div>
        )}
        {level === 'l2' && (
          <div className="kbv-stage kbv-stage-with-side">
            <div className="kbv-chart-card">
              <div ref={sunburstRef} style={{ width: '100%', height: '100%' }} />
            </div>
            <aside className="kbv-side-panel">
              <div className="kbv-panel-kicker">DRILLDOWN</div>
              <h3>{selCat} 子分类</h3>
              <p>点击信号卡进入明细，仍按服务端分页加载。</p>
              <div className="kbv-chip-cloud">
                {hotSubcategories.map((sub) => (
                  <button
                    key={sub.name}
                    className="kbv-chip"
                    onClick={() => {
                      startTransition(() => {
                        setSelSub(sub.name);
                        setLevel('l3');
                      });
                    }}
                  >
                    <span>{sub.name}</span>
                    <b>{sub.count}</b>
                  </button>
                ))}
              </div>
            </aside>
          </div>
        )}
        {level === 'l3' && (
          <div className="kbv-l3">
            <div
              className="kbv-toolbar"
            >
              <div>
                <ToolbarLabel text="关键词过滤" />
                <input
                  value={keywordInput}
                  onChange={(event) => setKeywordInput(event.target.value)}
                  placeholder="按标题、问题、答案、标签过滤当前子类"
                  style={{
                    width: '100%',
                    height: 40,
                    borderRadius: 8,
                    border: `1px solid ${COLORS.glow}`,
                    background: COLORS.card,
                    color: COLORS.text,
                    padding: '0 12px',
                    outline: 'none',
                  }}
                />
              </div>
              <div>
                <ToolbarLabel text="排序字段" />
                <select
                  value={sortBy}
                  onChange={(event) => setSortBy(event.target.value as SortBy)}
                  style={{
                    width: '100%',
                    height: 40,
                    borderRadius: 8,
                    border: `1px solid ${COLORS.glow}`,
                    background: COLORS.card,
                    color: COLORS.text,
                    padding: '0 12px',
                    outline: 'none',
                  }}
                >
                  <option value="call_count">按调用次数</option>
                  <option value="risk_level">按风险等级</option>
                  <option value="title">按标题名称</option>
                </select>
              </div>
              <div>
                <ToolbarLabel text="排序方向" />
                <select
                  value={sortOrder}
                  onChange={(event) => setSortOrder(event.target.value as SortOrder)}
                  style={{
                    width: '100%',
                    height: 40,
                    borderRadius: 8,
                    border: `1px solid ${COLORS.glow}`,
                    background: COLORS.card,
                    color: COLORS.text,
                    padding: '0 12px',
                    outline: 'none',
                  }}
                >
                  <option value="desc">从高到低</option>
                  <option value="asc">从低到高</option>
                </select>
              </div>
            </div>

            <div className="kbv-list-shell">
              <div className="kbv-list-head">
                <div style={{ fontSize: 14, color: COLORS.text2 }}>
                  {selCat} · {selSub} · 共 {l3Total} 条
                </div>
                <div style={{ color: COLORS.cyan, fontSize: 13 }}>已加载 {l3Entries.length} 条</div>
                {deferredKeyword && <div style={{ color: COLORS.amber, fontSize: 13 }}>过滤词: {deferredKeyword}</div>}
                {loadingMore && <div style={{ color: COLORS.emerald, fontSize: 13 }}>正在续载更多条目...</div>}
              </div>
              <div className="kbv-progress">
                <div className="kbv-progress-fill" style={{ width: `${loadedRate}%` }} />
              </div>

              {l3Error && (
                <div style={{ marginBottom: 12, color: COLORS.red, fontSize: 13 }}>
                  条目加载异常: {l3Error}
                </div>
              )}

              {l3Loading ? (
                <div style={{ color: COLORS.cyan }}>正在加载明细条目...</div>
              ) : l3Entries.length === 0 ? (
                <div style={{ color: COLORS.text2 }}>当前筛选条件下暂无条目。</div>
              ) : (
                <div
                  ref={listViewportRef}
                  onScroll={handleListScroll}
                  className="kbv-list-viewport"
                >
                  <div style={{ height: totalHeight, position: 'relative' }}>
                    {visibleEntries.map((entry, index) => renderRow(entry, startIndex + index))}
                  </div>
                </div>
              )}
            </div>

            <div className="kbv-footnote">
              <div style={{ color: COLORS.text2, fontSize: 12 }}>
                采用服务端分页 + 前端虚拟渲染，单次按 {PAGE_SIZE} 条增量载入，避免 3k 数据一次性塞入页面。
              </div>
              {hasMore && !l3Loading && (
                <button
                  onClick={() => { void loadMore(); }}
                  disabled={loadingMore}
                  className="kbv-primary-btn"
                >
                  {loadingMore ? '加载中...' : '继续加载'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {drawerOpen && drawerEntry && (
        <div
          className="kbv-drawer-backdrop"
          onClick={closeDrawer}
        >
          <aside
            className="kbv-drawer"
            aria-label="知识条目详情"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="kbv-drawer-head">
              <div>
                <div className="kbv-panel-kicker">ENTRY DETAIL</div>
                <div className="kbv-drawer-title">条目详情</div>
              </div>
              <button
                aria-label="关闭条目详情"
                className="kbv-drawer-close"
                onClick={closeDrawer}
              >
                ×
              </button>
            </div>

            <div className="kbv-drawer-hero">
              <div className={`kbv-drawer-status ${drawerEntry.called ? 'is-called' : 'is-idle'}`}>
                {drawerEntry.called ? `已调用 ${drawerEntry.call_count} 次` : '未调用'}
              </div>
              <h2>{drawerEntry.title || drawerEntry.id}</h2>
              <div className="kbv-drawer-id">{drawerEntry.id}</div>
            </div>

            <div className="kbv-drawer-grid">
              <div className="kbv-drawer-field">
                <span>分类</span>
                <strong>{drawerEntry.category || 'N/A'}</strong>
              </div>
              <div className="kbv-drawer-field">
                <span>子分类</span>
                <strong>{drawerEntry.subcategory || 'N/A'}</strong>
              </div>
              <div className="kbv-drawer-field">
                <span>风险等级</span>
                <strong>{drawerEntry.risk_level || 'N/A'}</strong>
              </div>
              <div className="kbv-drawer-field">
                <span>来源机构</span>
                <strong>{drawerEntry.source_org || 'N/A'}</strong>
              </div>
            </div>

            <section className="kbv-drawer-section">
              <h3>来源标题</h3>
              <p>{drawerEntry.source_title || 'N/A'}</p>
              {drawerEntry.source_url && (
                <a href={drawerEntry.source_url} target="_blank" rel="noreferrer">查看来源链接 →</a>
              )}
            </section>

            {drawerEntry.question && (
              <section className="kbv-drawer-section">
                <h3>关联问题</h3>
                <p>{drawerEntry.question}</p>
              </section>
            )}

            {drawerEntry.answer && (
              <section className="kbv-drawer-section">
                <h3>答案摘要</h3>
                <p className="kbv-drawer-answer">{drawerEntry.answer}</p>
              </section>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
