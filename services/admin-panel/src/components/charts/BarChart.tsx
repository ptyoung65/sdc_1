'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface BarData {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarData[];
  width?: number;
  height?: number;
  title: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  orientation?: 'horizontal' | 'vertical';
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  width = 600,
  height = 400,
  title,
  xAxisLabel = '',
  yAxisLabel = '',
  orientation = 'vertical'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 60, right: 50, bottom: 60, left: 70 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Color scale
    const colorScale = d3.scaleOrdinal<string>()
      .domain(data.map(d => d.label))
      .range(data.map(d => d.color) || d3.schemeCategory10);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .style('fill', '#1f2937')
      .text(title);

    if (orientation === 'vertical') {
      // Vertical bar chart
      const xScale = d3.scaleBand()
        .domain(data.map(d => d.label))
        .range([0, innerWidth])
        .padding(0.1);

      const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) || 0])
        .nice()
        .range([innerHeight, 0]);

      // Add axes
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');

      const yAxis = g.append('g')
        .call(d3.axisLeft(yScale));

      // Add bars
      const bars = g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.label)!)
        .attr('y', d => yScale(d.value))
        .attr('width', xScale.bandwidth())
        .attr('height', d => innerHeight - yScale(d.value))
        .attr('fill', d => colorScale(d.label))
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          // Brighten the bar
          const brightColor = d3.color(colorScale(d.label))?.brighter(0.3)?.toString() || colorScale(d.label);
          d3.select(this).attr('fill', brightColor);

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
            <div><strong>${d.label}</strong></div>
            <div>값: ${d.value.toLocaleString()}</div>
          `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
          d3.select(this).attr('fill', colorScale(d.label));
          d3.selectAll('.tooltip').remove();
        });

      // Add value labels on bars
      g.selectAll('.bar-label')
        .data(data)
        .enter().append('text')
        .attr('class', 'bar-label')
        .attr('x', d => xScale(d.label)! + xScale.bandwidth() / 2)
        .attr('y', d => yScale(d.value) - 5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#374151')
        .text(d => d.value.toLocaleString());

      // Add zoom functionality
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.5, 5])
        .extent([[0, 0], [width, height]])
        .on('zoom', (event) => {
          const newXScale = event.transform.rescaleX(xScale);
          
          // Update x-axis
          g.select('.x-axis').call(d3.axisBottom(newXScale) as any)
            .selectAll('text')
            .style('text-anchor', 'end')
            .attr('dx', '-.8em')
            .attr('dy', '.15em')
            .attr('transform', 'rotate(-45)');
          
          // Update bars
          bars.attr('x', d => newXScale(d.label)!)
            .attr('width', newXScale.bandwidth());
        });

      g.select('.x-axis').remove();
      g.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');

      svg.call(zoom);

    } else {
      // Horizontal bar chart
      const xScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) || 0])
        .nice()
        .range([0, innerWidth]);

      const yScale = d3.scaleBand()
        .domain(data.map(d => d.label))
        .range([0, innerHeight])
        .padding(0.1);

      // Add axes
      const xAxis = g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(xScale));

      const yAxis = g.append('g')
        .call(d3.axisLeft(yScale));

      // Add bars
      const bars = g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', d => yScale(d.label)!)
        .attr('width', d => xScale(d.value))
        .attr('height', yScale.bandwidth())
        .attr('fill', d => colorScale(d.label))
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          const brightColor = d3.color(colorScale(d.label))?.brighter(0.3)?.toString() || colorScale(d.label);
          d3.select(this).attr('fill', brightColor);

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
            <div><strong>${d.label}</strong></div>
            <div>값: ${d.value.toLocaleString()}</div>
          `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
          d3.select(this).attr('fill', colorScale(d.label));
          d3.selectAll('.tooltip').remove();
        });

      // Add value labels on bars
      g.selectAll('.bar-label')
        .data(data)
        .enter().append('text')
        .attr('class', 'bar-label')
        .attr('x', d => xScale(d.value) + 5)
        .attr('y', d => yScale(d.label)! + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#374151')
        .text(d => d.value.toLocaleString());

      // Add zoom functionality for horizontal chart
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.5, 5])
        .extent([[0, 0], [width, height]])
        .on('zoom', (event) => {
          const newXScale = event.transform.rescaleX(xScale);
          
          // Update x-axis
          xAxis.call(d3.axisBottom(newXScale) as any);
          
          // Update bars
          bars.attr('width', d => newXScale(d.value));
        });

      svg.call(zoom);
    }

    // Add axis labels
    if (xAxisLabel) {
      g.append('text')
        .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + margin.bottom - 10})`)
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#6b7280')
        .text(xAxisLabel);
    }

    if (yAxisLabel) {
      g.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - (innerHeight / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#6b7280')
        .text(yAxisLabel);
    }

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
        svg.transition().call(
          d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
          1.2
        );
      });

    controls.append('button')
      .text('축소')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(
          d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
          0.8
        );
      });

    controls.append('button')
      .text('리셋')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('border', '1px solid #d1d5db')
      .style('background', 'white')
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().call(
          d3.zoom<SVGSVGElement, unknown>().transform as any,
          d3.zoomIdentity
        );
      });

  }, [data, width, height, title, xAxisLabel, yAxisLabel, orientation]);

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

export default BarChart;