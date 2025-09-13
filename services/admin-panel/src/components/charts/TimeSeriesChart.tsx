'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

interface TimeSeriesChartProps {
  data: TimeSeriesData[];
  width?: number;
  height?: number;
  title: string;
  color?: string;
  yAxisLabel?: string;
}

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  width = 800,
  height = 400,
  title,
  color = '#3b82f6',
  yAxisLabel = 'Value'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous chart

    const margin = { top: 60, right: 50, bottom: 60, left: 70 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Parse dates
    const parseTime = d3.timeParse('%Y-%m-%dT%H:%M:%S');
    const processedData = data.map(d => ({
      ...d,
      timestamp: parseTime(d.timestamp.split('.')[0]) || new Date(),
      value: +d.value
    }));

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(processedData, d => d.timestamp) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(processedData, d => d.value) as [number, number])
      .nice()
      .range([innerHeight, 0]);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add clip path for zooming
    svg.append('defs')
      .append('clipPath')
      .attr('id', `clip-${title.replace(/\s+/g, '-')}`)
      .append('rect')
      .attr('width', innerWidth)
      .attr('height', innerHeight);

    // Create line generator
    const line = d3.line<any>()
      .x(d => xScale(d.timestamp))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX);

    // Add axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%H:%M')));

    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale));

    // Add axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text(yAxisLabel);

    g.append('text')
      .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('시간');

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .style('fill', '#1f2937')
      .text(title);

    // Add the line
    const path = g.append('path')
      .datum(processedData)
      .attr('clip-path', `url(#clip-${title.replace(/\s+/g, '-')})`)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2)
      .attr('d', line);

    // Add dots
    const dots = g.selectAll('.dot')
      .data(processedData)
      .enter().append('circle')
      .attr('class', 'dot')
      .attr('clip-path', `url(#clip-${title.replace(/\s+/g, '-')})`)
      .attr('cx', d => xScale(d.timestamp))
      .attr('cy', d => yScale(d.value))
      .attr('r', 4)
      .attr('fill', color)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
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

        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.html(`
          <div>시간: ${d3.timeFormat('%Y-%m-%d %H:%M')(d.timestamp)}</div>
          <div>값: ${d.value.toFixed(2)}</div>
          ${d.label ? `<div>${d.label}</div>` : ''}
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');

        const brightColor = d3.color(color)?.brighter(0.5)?.toString() || color;
        d3.select(this).attr('r', 6).attr('fill', brightColor);
      })
      .on('mouseout', function() {
        d3.selectAll('.tooltip').remove();
        d3.select(this).attr('r', 4).attr('fill', color);
      });

    // Add zoom functionality
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 10])
      .extent([[0, 0], [width, height]])
      .on('zoom', (event) => {
        const newXScale = event.transform.rescaleX(xScale);
        
        // Update axes
        xAxis.call(d3.axisBottom(newXScale).tickFormat(d3.timeFormat('%H:%M')) as any);
        
        // Update line
        const newLine = d3.line<any>()
          .x(d => newXScale(d.timestamp))
          .y(d => yScale(d.value))
          .curve(d3.curveMonotoneX);
        
        path.attr('d', newLine(processedData));
        
        // Update dots
        dots.attr('cx', d => newXScale(d.timestamp));
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
        svg.transition().call(zoom.scaleBy, 1.5);
      });

    controls.append('button')
      .text('축소')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(zoom.scaleBy, 0.67);
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

  }, [data, width, height, title, color, yAxisLabel]);

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

export default TimeSeriesChart;