import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import * as echarts from 'echarts/core';
import { ScatterChart, SunburstChart } from 'echarts/charts';
import { TooltipComponent, TitleComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { List } from 'react-window';
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
  source_org: string;
  source_url: string;
  question: string;
  answer: string;
}

const COLORS = {
  bg: '#0f172a',
  card: '#1e293b',
  text: '#f1f5f9',
  text2: '#94a3b8',
  cyan: '#06b6d4',
  emerald: '#10b981',
  red: '#ef4444',
  glow: 'rgba(6, 182, 212, 0.3)',
};

function useKBSummary() {
  const [data, setData] = useState<KBSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    jsonFetch<KBSummary>('/api/kb/summary')
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e instanceof Error ? e.message : String(e)); setLoading(false); });
  }, []);

  return { data, loading, error };
}

function useKBEntries(category: string, subcategory: string) {
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!category) { setEntries([]); setLoading(false); return; }
    const params = new URLSearchParams();
    params.set('category', category);
    if (subcategory) params.set('subcategory', subcategory);
    params.set('limit', '200');
    jsonFetch<{ entries: KBEntry[] }>(`/api/kb/entries?${params.toString()}`)
      .then((d) => { setEntries(d.entries || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [category, subcategory]);

  return { entries, loading };
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="stat-card" style={{ background: COLORS.card, borderRadius: 12, padding: '16px 20px', border: `1px solid ${COLORS.glow}` }}>
      <div style={{ color: COLORS.text2, fontSize: 13, marginBottom: 6 }}>{label}</div>
      <div style={{ color: color || COLORS.cyan, fontSize: 28, fontWeight: 700, fontFamily: 'monospace' }}>{value}</div>
    </div>
  );
}

export default function KBVisualization() {
  const { data, loading, error } = useKBSummary();
  const [level, setLevel] = useState<'l1' | 'l2' | 'l3'>('l1');
  const [selCat, setSelCat] = useState('');
  const [selSub, setSelSub] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerEntry, setDrawerEntry] = useState<KBEntry | null>(null);

  const bubbleRef = useRef<HTMLDivElement>(null);
  const sunburstRef = useRef<HTMLDivElement>(null);
  const bubbleChart = useRef<echarts.ECharts | null>(null);
  const sunburstChart = useRef<echarts.ECharts | null>(null);

  // L1 Bubble Chart
  useEffect(() => {
    if (!data || level !== 'l1' || !bubbleRef.current) return;
    if (bubbleChart.current) { bubbleChart.current.dispose(); }
    const chart = echarts.init(bubbleRef.current, undefined, { renderer: 'canvas' });
    bubbleChart.current = chart;

    const cats = data.categories;
    const maxCount = Math.max(...cats.map((c) => c.count), 1);
    const seriesData = cats.map((c, i) => ({
      name: c.name,
      value: [i, c.count, c.count, c.coverage_rate],
      itemStyle: {
        color: c.coverage_rate > 0
          ? `rgba(16, 185, 129, ${0.4 + c.coverage_rate / 200})`
          : `rgba(239, 68, 68, 0.5)`,
        borderColor: c.coverage_rate > 0 ? COLORS.emerald : COLORS.red,
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: c.coverage_rate > 0 ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
      },
    }));

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '知识库分类全景', left: 'center', textStyle: { color: COLORS.text, fontSize: 18 } },
      tooltip: {
        backgroundColor: COLORS.card,
        borderColor: COLORS.cyan,
        textStyle: { color: COLORS.text },
        formatter: (p: any) => {
          const c = cats[p.dataIndex];
          return `<b>${c.name}</b><br/>条目数: ${c.count}<br/>已调用: ${c.called_count}<br/>覆盖率: ${c.coverage_rate}%`;
        },
      },
      grid: { left: 40, right: 40, top: 60, bottom: 40 },
      xAxis: {
        type: 'category',
        data: cats.map((c) => c.name),
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
        symbolSize: (d: any) => Math.max(20, (d[2] / maxCount) * 80),
        data: seriesData,
        emphasis: {
          itemStyle: { shadowBlur: 20, shadowColor: COLORS.cyan },
        },
      }],
    });

    chart.on('click', (params: any) => {
      const cat = cats[params.dataIndex];
      if (cat) { setSelCat(cat.name); setLevel('l2'); }
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); chart.dispose(); };
  }, [data, level]);

  // L2 Sunburst
  const catData = useMemo(() => data?.categories.find((c) => c.name === selCat), [data, selCat]);

  useEffect(() => {
    if (!catData || level !== 'l2' || !sunburstRef.current) return;
    if (sunburstChart.current) { sunburstChart.current.dispose(); }
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
        formatter: (p: any) => {
          const sub = catData.subcategories.find((s) => s.name === p.name);
          if (!sub) return p.name;
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

    chart.on('click', (params: any) => {
      setSelSub(params.name);
      setLevel('l3');
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); chart.dispose(); };
  }, [catData, level, selCat]);

  // L3 Virtual List
  const { entries: l3Entries, loading: l3Loading } = useKBEntries(selCat, selSub);

  const openDrawer = useCallback((entry: KBEntry) => {
    setDrawerEntry(entry);
    setDrawerOpen(true);
  }, []);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const e = l3Entries[index];
    if (!e) return null;
    return (
      <div style={{ ...style, padding: '0 12px' }}>
        <div
          onClick={() => openDrawer(e as unknown as KBEntry)}
          style={{
            background: COLORS.card,
            borderRadius: 8,
            padding: '12px 16px',
            marginBottom: 8,
            border: `1px solid ${e.called ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: e.called ? COLORS.emerald : COLORS.red,
            boxShadow: `0 0 8px ${e.called ? COLORS.emerald : COLORS.red}`,
            flexShrink: 0,
          }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: COLORS.text, fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {e.title || e.id}
            </div>
            <div style={{ color: COLORS.text2, fontSize: 12, marginTop: 2 }}>
              {e.category} · {e.subcategory} · 风险等级: {e.risk_level || 'N/A'}
            </div>
          </div>
          <div style={{ color: e.called ? COLORS.emerald : COLORS.red, fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
            {e.called ? `已调用 ${e.call_count || ''}` : '未调用'}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: COLORS.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: COLORS.cyan }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>Loading KB Data...</div>
          <div style={{ width: 200, height: 3, background: COLORS.card, borderRadius: 2, margin: '0 auto' }}>
            <div style={{ width: '60%', height: '100%', background: COLORS.cyan, borderRadius: 2, animation: 'pulse 1.5s infinite' }} />
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
    <div style={{ width: '100vw', height: '100vh', background: COLORS.bg, color: COLORS.text, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Top Bar */}
      <div style={{ height: 56, borderBottom: `1px solid ${COLORS.glow}`, display: 'flex', alignItems: 'center', padding: '0 20px', gap: 16, flexShrink: 0 }}>
        <a href="#/" style={{ color: COLORS.cyan, textDecoration: 'none', fontSize: 14, fontWeight: 600 }}>← 返回对话</a>
        <div style={{ width: 1, height: 20, background: COLORS.text2 }} />
        <div style={{ fontSize: 16, fontWeight: 700 }}>知识库态势感知</div>
        <div style={{ flex: 1 }} />
        {level !== 'l1' && (
          <button
            onClick={() => { setLevel(level === 'l3' ? 'l2' : 'l1'); if (level === 'l3') setSelSub(''); }}
            style={{ background: 'transparent', border: `1px solid ${COLORS.cyan}`, color: COLORS.cyan, padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}
          >
            ← 返回上级
          </button>
        )}
        <div style={{ color: COLORS.text2, fontSize: 12 }}>
          {level === 'l1' ? '全景视图' : level === 'l2' ? `${selCat}` : `${selCat} > ${selSub}`}
        </div>
      </div>

      {/* Stats Bar */}
      <div style={{ display: 'flex', gap: 12, padding: '16px 20px', flexShrink: 0, overflowX: 'auto' }}>
        <StatCard label="总条目" value={data.total_entries} />
        <StatCard label="分类数" value={data.total_categories} />
        <StatCard label="已调用" value={data.called_entries} color={COLORS.emerald} />
        <StatCard label="未调用" value={data.total_entries - data.called_entries} color={COLORS.red} />
        <StatCard label="覆盖率" value={`${data.coverage_rate}%`} color={COLORS.cyan} />
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '0 20px 20px', minHeight: 0, position: 'relative' }}>
        {level === 'l1' && (
          <div ref={bubbleRef} style={{ width: '100%', height: '100%' }} />
        )}
        {level === 'l2' && (
          <div ref={sunburstRef} style={{ width: '100%', height: '100%' }} />
        )}
        {level === 'l3' && (
          <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: 12, fontSize: 14, color: COLORS.text2 }}>
              {selCat} · {selSub} · 共 {l3Entries.length} 条
            </div>
            {l3Loading ? (
              <div style={{ color: COLORS.cyan }}>加载中...</div>
            ) : (
              <List
                height={window.innerHeight - 220}
                itemCount={l3Entries.length}
                itemSize={80}
                width="100%"
              >
                {Row}
              </List>
            )}
          </div>
        )}
      </div>

      {/* Detail Drawer */}
      {drawerOpen && drawerEntry && (
        <div style={{
          position: 'fixed', top: 0, right: 0, width: 420, height: '100vh',
          background: COLORS.card, borderLeft: `1px solid ${COLORS.glow}`,
          zIndex: 1000, padding: 24, overflowY: 'auto',
          boxShadow: '-10px 0 40px rgba(0,0,0,0.5)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div style={{ fontSize: 16, fontWeight: 700 }}>条目详情</div>
            <button onClick={() => setDrawerOpen(false)} style={{ background: 'transparent', border: 'none', color: COLORS.text2, fontSize: 20, cursor: 'pointer' }}>×</button>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>ID</div>
            <div style={{ fontSize: 14, fontFamily: 'monospace' }}>{drawerEntry.id}</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>标题</div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{drawerEntry.title}</div>
          </div>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>分类</div>
              <div>{drawerEntry.category}</div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>子分类</div>
              <div>{drawerEntry.subcategory}</div>
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>风险等级</div>
            <div>{drawerEntry.risk_level || 'N/A'}</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>调用状态</div>
            <div style={{ color: drawerEntry.called ? COLORS.emerald : COLORS.red, fontWeight: 600 }}>
              {drawerEntry.called ? `已调用 (${drawerEntry.call_count} 次)` : '未调用'}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>来源</div>
            <div>{drawerEntry.source_org || 'N/A'}</div>
          </div>
          {drawerEntry.source_url && (
            <div style={{ marginBottom: 16 }}>
              <a href={drawerEntry.source_url} target="_blank" rel="noreferrer" style={{ color: COLORS.cyan, fontSize: 13 }}>查看来源链接 →</a>
            </div>
          )}
          {drawerEntry.question && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>关联问题</div>
              <div style={{ fontSize: 13, lineHeight: 1.5 }}>{drawerEntry.question}</div>
            </div>
          )}
          {drawerEntry.answer && (
            <div>
              <div style={{ color: COLORS.text2, fontSize: 12, marginBottom: 4 }}>答案摘要</div>
              <div style={{ fontSize: 13, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{drawerEntry.answer}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
