/**
 * Network Page - Interactive D3 force-directed graph + cascade chain visualization.
 * Supports drag, zoom/pan, and hover tooltips.
 */

import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import type { PersonNode, MeetingEdge } from '@/types/api';

function truncateEmail(email: string): string {
  return email.length > 20 ? email.slice(0, 17) + '...' : email;
}

interface NetworkVizProps {
  nodes: PersonNode[];
  edges: MeetingEdge[];
}

function NetworkViz({ nodes, edges }: NetworkVizProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !nodes.length) return;

    import('d3').then((d3) => {
      if (!svgRef.current || !containerRef.current) return;

      const width = svgRef.current.clientWidth || 600;
      const height = 500;

      const svg = d3
        .select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      svg.selectAll('*').remove();

      // Wrap everything in a <g> so zoom can transform it
      const g = svg.append('g');

      const nodeColor = (n: PersonNode) => {
        if (n.at_risk) return '#FF8FA3'; // coral — at risk
        if (n.focus_percentage < 0.35) return '#FFD4B8'; // peach — borderline
        if (n.focus_percentage >= 0.6) return '#A8EED4'; // mint — healthy
        return '#C8B8F8'; // lavender — moderate
      };

      const nodeRadius = (n: PersonNode) =>
        Math.max(16, Math.min(42, 10 + n.total_meeting_hours * 1.8));

      type SimNode = PersonNode & d3.SimulationNodeDatum;
      type SimLink = d3.SimulationLinkDatum<SimNode> & { value: number };

      const simNodes: SimNode[] = nodes.map((n) => ({ ...n }));
      const nodeById = new Map(simNodes.map((n) => [n.email, n]));

      const simLinks: SimLink[] = edges
        .filter((e) => nodeById.has(e.person_a) && nodeById.has(e.person_b))
        .map((e) => ({
          source: nodeById.get(e.person_a)!,
          target: nodeById.get(e.person_b)!,
          value: e.co_occurrence_count,
        }));

      const simulation = d3
        .forceSimulation<SimNode>(simNodes)
        .force(
          'link',
          d3.forceLink<SimNode, SimLink>(simLinks).id((d) => d.email).distance(90),
        )
        .force('charge', d3.forceManyBody().strength(-250))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide<SimNode>().radius((d) => nodeRadius(d) + 10));

      const link = g
        .append('g')
        .selectAll<SVGLineElement, SimLink>('line')
        .data(simLinks)
        .join('line')
        .attr('stroke', '#000000')
        .attr('stroke-width', (d) => Math.max(1, Math.min(5, d.value / 2)))
        .attr('stroke-opacity', 0.35);

      const node = g
        .append('g')
        .selectAll<SVGCircleElement, SimNode>('circle')
        .data(simNodes)
        .join('circle')
        .attr('r', (d) => nodeRadius(d))
        .attr('fill', (d) => nodeColor(d))
        .attr('stroke', '#000000')
        .attr('stroke-width', 3)
        .style('cursor', 'grab');

      const label = g
        .append('g')
        .selectAll<SVGTextElement, SimNode>('text')
        .data(simNodes)
        .join('text')
        .text((d) => d.display_name.split(' ')[0].charAt(0) + d.display_name.split(' ').slice(-1)[0].charAt(0))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('font-family', 'JetBrains Mono, monospace')
        .attr('font-weight', 'bold')
        .attr('font-size', 12)
        .attr('fill', '#000000')
        .style('pointer-events', 'none')
        .style('user-select', 'none');

      // Tick handler
      simulation.on('tick', () => {
        link
          .attr('x1', (d) => (d.source as SimNode).x ?? 0)
          .attr('y1', (d) => (d.source as SimNode).y ?? 0)
          .attr('x2', (d) => (d.target as SimNode).x ?? 0)
          .attr('y2', (d) => (d.target as SimNode).y ?? 0);

        node.attr('cx', (d) => d.x ?? 0).attr('cy', (d) => d.y ?? 0);
        label.attr('x', (d) => d.x ?? 0).attr('y', (d) => d.y ?? 0);
      });

      // ── Drag ────────────────────────────────────────────────────────────────
      const drag = d3
        .drag<SVGCircleElement, SimNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
          d3.select(event.sourceEvent.target).style('cursor', 'grabbing');
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
          d3.select(event.sourceEvent.target).style('cursor', 'grab');
        });

      node.call(drag);

      // ── Zoom / pan ───────────────────────────────────────────────────────────
      const zoomBehavior = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.25, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform.toString());
        });

      svg.call(zoomBehavior).on('dblclick.zoom', null); // disable double-click zoom

      // ── Hover tooltip ────────────────────────────────────────────────────────
      node
        .on('mouseover', (event: MouseEvent, d: SimNode) => {
          const tip = tooltipRef.current;
          const container = containerRef.current;
          if (!tip || !container) return;
          const rect = container.getBoundingClientRect();
          const focusPct = Math.round(d.focus_percentage * 100);
          const atRiskLabel = d.at_risk ? '<span style="color:#FF8FA3;font-weight:bold"> ⚠ AT RISK</span>' : '';
          tip.innerHTML = `
            <div style="font-weight:700;margin-bottom:4px">${d.display_name}${atRiskLabel}</div>
            <div style="opacity:0.6;font-size:10px;margin-bottom:6px">${d.email}</div>
            <div>🕐 ${d.total_meeting_hours.toFixed(1)}h in meetings</div>
            <div>🎯 ${focusPct}% focus time</div>
            <div>📊 Centrality: ${(d.centrality_score * 100).toFixed(0)}%</div>
          `;
          tip.style.opacity = '1';
          tip.style.left = (event.clientX - rect.left + 12) + 'px';
          tip.style.top = (event.clientY - rect.top - 10) + 'px';
        })
        .on('mousemove', (event: MouseEvent) => {
          const tip = tooltipRef.current;
          const container = containerRef.current;
          if (!tip || !container) return;
          const rect = container.getBoundingClientRect();
          tip.style.left = (event.clientX - rect.left + 12) + 'px';
          tip.style.top = (event.clientY - rect.top - 10) + 'px';
        })
        .on('mouseout', () => {
          if (tooltipRef.current) tooltipRef.current.style.opacity = '0';
        });

      return () => {
        simulation.stop();
      };
    });
  }, [nodes, edges]);

  return (
    <div ref={containerRef} className="relative w-full" style={{ height: '500px' }}>
      <svg ref={svgRef} className="w-full h-full" />
      {/* Tooltip bubble */}
      <div
        ref={tooltipRef}
        className="absolute pointer-events-none z-10 bg-kb-black text-kb-white font-mono text-xs p-3 leading-relaxed max-w-[200px] transition-opacity duration-100"
        style={{ opacity: 0 }}
      />
      {/* Interaction hint */}
      <div className="absolute bottom-3 right-3 font-mono text-xs text-kb-black/30 select-none">
        drag nodes · scroll to zoom
      </div>
    </div>
  );
}

function ColorLegend() {
  const items = [
    { color: '#FF8FA3', label: 'At risk (focus &lt; 15%)' },
    { color: '#FFD4B8', label: 'Borderline (focus &lt; 35%)' },
    { color: '#C8B8F8', label: 'Moderate' },
    { color: '#A8EED4', label: 'Healthy (focus ≥ 60%)' },
  ];
  return (
    <div className="flex flex-wrap gap-3 px-4 py-3 bg-kb-white border-t-2 border-kb-black">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <div
            className="w-3 h-3 rounded-full border-2 border-kb-black flex-shrink-0"
            style={{ backgroundColor: item.color }}
          />
          <span
            className="font-mono text-xs text-kb-black/60"
            dangerouslySetInnerHTML={{ __html: item.label }}
          />
        </div>
      ))}
      <div className="flex items-center gap-1.5 ml-auto">
        <div className="w-8 h-0.5 bg-kb-black/40" style={{ borderTop: '2px solid rgba(0,0,0,0.2)' }} />
        <span className="font-mono text-xs text-kb-black/40">thicker = more co-meetings</span>
      </div>
    </div>
  );
}

export function Network() {
  const { results } = useSession();
  const meetingTitleMap = new Map<string, string>(
    (results?.meetings ?? []).map((m) => [m.meeting_id, m.title]),
  );

  if (!results || results.status !== 'complete') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing'
            ? 'ANALYSIS IN PROGRESS...'
            : 'RUN AN ANALYSIS TO SEE YOUR MEETING NETWORK'}
        </p>
        <Link
          to="/settings"
          className="border-2 border-kb-black bg-kb-pink px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          {results?.status === 'processing' ? 'View Progress' : 'Go to Settings'}
        </Link>
      </div>
    );
  }

  if (!results.network_graph) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-black text-3xl uppercase">NETWORK</h1>
        </div>
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-12 text-center">
          <div className="font-mono text-4xl mb-4">🕸️</div>
          <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black/60">
            NOT ENOUGH DATA FOR A NETWORK GRAPH
          </p>
        </div>
      </div>
    );
  }

  const { nodes, edges, most_central_person, highest_cost_pair } = results.network_graph;
  const topEdges = [...edges]
    .sort((a, b) => b.co_occurrence_count - a.co_occurrence_count)
    .slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-black text-3xl uppercase">NETWORK</h1>
        <span className="bg-kb-lavender border-2 border-kb-black px-4 py-2 font-mono font-bold text-xs uppercase shadow-brutal-sm">
          {nodes.length} PEOPLE · {edges.length} CONNECTIONS
        </span>
      </div>

      <div className="grid grid-cols-3 gap-8 mb-8">
        {/* Network viz (col-span-2) */}
        <div className="col-span-2 border-3 border-kb-black shadow-brutal-lg bg-kb-white overflow-hidden">
          <div className="bg-kb-black px-4 py-2 border-b-2 border-kb-black flex items-center justify-between">
            <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-white">
              MEETING NETWORK GRAPH
            </span>
            <span className="font-mono text-xs text-kb-white/50">
              Node size = meeting hours · Color = focus time
            </span>
          </div>
          <NetworkViz nodes={nodes} edges={edges} />
          <ColorLegend />
        </div>

        {/* Right sidebar */}
        <div className="space-y-6">
          {/* Top connections */}
          <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
            <h2 className="font-display font-black text-lg uppercase mb-4 text-kb-black">
              TOP CONNECTIONS
            </h2>
            <p className="font-sans text-xs text-kb-black/50 mb-3">
              Pairs who share the most meetings together
            </p>
            <div className="space-y-3">
              {topEdges.map((edge, idx) => (
                <div
                  key={idx}
                  className="border-b-2 border-kb-black pb-3 last:border-b-0 last:pb-0 flex items-center gap-2 flex-wrap"
                >
                  <span className="font-mono text-xs text-kb-black truncate max-w-[90px]" title={edge.person_a}>
                    {truncateEmail(edge.person_a)}
                  </span>
                  <span className="font-mono font-bold text-kb-black">↔</span>
                  <span className="font-mono text-xs text-kb-black truncate max-w-[90px]" title={edge.person_b}>
                    {truncateEmail(edge.person_b)}
                  </span>
                  <span className="bg-kb-lavender border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs ml-auto flex-shrink-0">
                    {edge.co_occurrence_count}×
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Most central */}
          <div className="bg-kb-lavender border-3 border-kb-black shadow-brutal-md p-6">
            <h2 className="font-display font-black text-base uppercase mb-1 text-kb-black">
              MOST CENTRAL
            </h2>
            <p className="font-sans text-xs text-kb-black/60 mb-2">
              Attends the broadest mix of meetings — removing them would fragment the team's coordination.
            </p>
            <div className="font-mono font-bold text-sm text-kb-black break-all">
              {most_central_person}
            </div>
          </div>

          {/* Highest cost pair */}
          <div className="bg-kb-coral border-3 border-kb-black shadow-brutal-md p-6">
            <h2 className="font-display font-black text-base uppercase mb-1 text-kb-black">
              HIGHEST COST PAIR
            </h2>
            <p className="font-sans text-xs text-kb-black/70 mb-2">
              Two people whose shared meetings cost the most in combined salary time.
            </p>
            <div className="font-mono font-bold text-sm text-kb-black space-y-1">
              <div className="break-all">{highest_cost_pair[0]}</div>
              <div className="text-kb-black/50">↔</div>
              <div className="break-all">{highest_cost_pair[1]}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Cascade chains */}
      {results.cascade_chains.length > 0 && (
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
          <div className="flex items-start gap-3 mb-6">
            <h2 className="font-display font-black text-xl uppercase text-kb-black">
              CASCADE CHAINS
            </h2>
            <div className="bg-kb-peach border-2 border-kb-black px-3 py-1 font-mono text-xs font-bold uppercase">
              {results.cascade_chains.length} DETECTED
            </div>
          </div>
          <p className="font-sans text-sm text-kb-black/60 mb-5 max-w-2xl">
            A cascade chain starts when a meeting ends without clear decisions — and a follow-up meeting is booked within 72 hours with 40%+ of the same attendees. The original meeting spawned the follow-ups below.
          </p>
          <div className="space-y-4">
            {results.cascade_chains.map((chain, idx) => {
              const originTitle =
                meetingTitleMap.get(chain.origin_meeting_id) ??
                `...${chain.origin_meeting_id.slice(-8)}`;
              return (
                <div key={idx} className="border-b-2 border-kb-black pb-4 last:border-b-0 last:pb-0">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className="bg-kb-peach border-2 border-kb-black px-3 py-1 font-mono text-xs font-bold uppercase">
                      ORIGIN
                    </span>
                    <span className="font-mono font-bold text-sm text-kb-black">{originTitle}</span>
                    <span className="bg-kb-coral border-2 border-kb-black px-2 py-0.5 font-mono text-xs font-bold uppercase ml-auto">
                      ${chain.total_cascade_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}{' '}
                      TOTAL COST · DEPTH {chain.cascade_depth}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap pl-4">
                    {chain.spawned_meeting_ids.map((sid) => (
                      <span
                        key={sid}
                        className="bg-kb-lavender border-2 border-kb-black px-2 py-0.5 font-mono text-xs font-bold"
                      >
                        → {meetingTitleMap.get(sid) ?? `...${sid.slice(-8)}`}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Made with Bob
