'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface DonutData {
  label: string;
  value: number;
  color?: string;
}

interface DonutChartProps {
  data: DonutData[];
  width?: number;
  height?: number;
  title: string;
  innerRadius?: number;
  outerRadius?: number;
}

const DonutChart: React.FC<DonutChartProps> = ({
  data,
  width = 400,
  height = 400,
  title,
  innerRadius,
  outerRadius
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = 40;
    const radius = Math.min(width, height) / 2 - margin;
    const defaultInnerRadius = innerRadius || radius * 0.4;
    const defaultOuterRadius = outerRadius || radius;

    // Color scale
    const colorScale = d3.scaleOrdinal<string>()
      .domain(data.map(d => d.label))
      .range(data.map(d => d.color) || d3.schemeSet3);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .style('fill', '#1f2937')
      .text(title);

    // Create pie generator
    const pie = d3.pie<DonutData>()
      .value(d => d.value)
      .sort(null);

    // Create arc generator
    const arc = d3.arc<d3.PieArcDatum<DonutData>>()
      .innerRadius(defaultInnerRadius)
      .outerRadius(defaultOuterRadius);

    // Create arc for hover effect
    const arcHover = d3.arc<d3.PieArcDatum<DonutData>>()
      .innerRadius(defaultInnerRadius)
      .outerRadius(defaultOuterRadius + 10);

    // Create the arcs
    const arcs = g.selectAll('.arc')
      .data(pie(data))
      .enter().append('g')
      .attr('class', 'arc')
      .style('cursor', 'pointer');

    // Add the paths
    const paths = arcs.append('path')
      .attr('d', arc)
      .attr('fill', d => colorScale(d.data.label))
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .on('mouseover', function(event, d) {
        // Expand arc
        d3.select(this)
          .transition()
          .duration(200)
          .attr('d', arcHover);

        // Create tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('opacity', 0);

        const total = d3.sum(data, d => d.value);
        const percentage = ((d.data.value / total) * 100).toFixed(1);

        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.html(`
          <div><strong>${d.data.label}</strong></div>
          <div>값: ${d.data.value}</div>
          <div>비율: ${percentage}%</div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function(event, d) {
        // Return to normal size
        d3.select(this)
          .transition()
          .duration(200)
          .attr('d', arc);

        // Remove tooltip
        d3.selectAll('.tooltip').remove();
      });

    // Add labels
    arcs.append('text')
      .attr('transform', d => `translate(${arc.centroid(d)})`)
      .attr('dy', '0.35em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', 'white')
      .text(d => {
        const total = d3.sum(data, d => d.value);
        const percentage = ((d.data.value / total) * 100).toFixed(0);
        return percentage + '%';
      });

    // Add center text (total)
    const total = d3.sum(data, d => d.value);
    const centerGroup = g.append('g')
      .attr('class', 'center-text');

    centerGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.5em')
      .style('font-size', '24px')
      .style('font-weight', 'bold')
      .style('fill', '#1f2937')
      .text(total.toLocaleString());

    centerGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1em')
      .style('font-size', '14px')
      .style('fill', '#6b7280')
      .text('총계');

    // Add legend
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(20, 60)`);

    const legendItems = legend.selectAll('.legend-item')
      .data(data)
      .enter().append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`)
      .style('cursor', 'pointer')
      .on('click', function(event, d) {
        // Toggle visibility of the corresponding arc
        const arcElement = arcs.filter(arcData => arcData.data.label === d.label);
        const path = arcElement.select('path');
        const text = arcElement.select('text');
        
        const isVisible = path.style('opacity') !== '0.3';
        
        path.style('opacity', isVisible ? '0.3' : '1');
        text.style('opacity', isVisible ? '0.3' : '1');
        
        d3.select(this).select('rect')
          .style('opacity', isVisible ? '0.3' : '1');
        d3.select(this).select('text')
          .style('opacity', isVisible ? '0.3' : '1');
      });

    legendItems.append('rect')
      .attr('width', 12)
      .attr('height', 12)
      .attr('fill', d => colorScale(d.label));

    legendItems.append('text')
      .attr('x', 18)
      .attr('y', 6)
      .attr('dy', '0.35em')
      .style('font-size', '12px')
      .style('fill', '#374151')
      .text(d => d.label);

    // Add zoom functionality (for the entire chart)
    let currentScale = 1;
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        currentScale = event.transform.k;
        g.attr('transform', `translate(${width / 2},${height / 2}) scale(${currentScale})`);
      });

    svg.call(zoom);

    // Add zoom controls
    const controls = d3.select(containerRef.current)
      .select('.chart-controls')
      .style('position', 'absolute')
      .style('top', '10px')
      .style('right', '10px')
      .style('display', 'flex')
      .style('gap', '5px');

    controls.selectAll('*').remove();

    controls.append('button')
      .text('확대')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(zoom.scaleBy, 1.2);
      });

    controls.append('button')
      .text('축소')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(zoom.scaleBy, 0.8);
      });

    controls.append('button')
      .text('리셋')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(zoom.transform, d3.zoomIdentity);
      });

  }, [data, width, height, title, innerRadius, outerRadius]);

  return (
    <div ref={containerRef} className="relative">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #e5e7eb', borderRadius: '8px' }}
      />
      <div className="chart-controls"></div>
    </div>
  );
};

export default DonutChart;