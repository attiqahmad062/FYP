import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

const ForceDirectedGraph = () => {
  const svgRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  // Fetch data from API
  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5001/all-entries", {
          signal: controller.signal,
        });
        const data = await response.json();

        if (data.status === "success") {
          const { groups, techniques } = data.data;
          const nodes = [];
          const links = [];
          const nodeMap = new Map();

          // Process groups
          groups.forEach((group) => {
            if (!nodeMap.has(group.id)) {
              const node = {
                id: group.id,
                name: group.name,
                type: "group",
              };
              nodes.push(node);
              nodeMap.set(group.id, node);
            }
          });

          // Process techniques
          techniques.forEach((technique) => {
            const techId = technique.id.split("/").pop() || technique.id;
            if (!nodeMap.has(techId)) {
              const node = {
                id: techId,
                type: "technique",
              };
              nodes.push(node);
              nodeMap.set(techId, node);
            }

            // Create links
            technique.groups?.forEach((groupId) => {
              links.push({
                source: groupId,
                target: techId,
              });
            });
          });

          setGraphData({ nodes, links });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("Fetch error:", error);
        }
      }
    };

    fetchData();
    return () => controller.abort();
  }, []);

  // D3 visualization
  useEffect(() => {
    if (!svgRef.current || graphData.nodes.length === 0) return;

    const width = 1000;
    const height = 800;
    const svg = d3.select(svgRef.current)
      .html("")
      .attr("width", width)
      .attr("height", height);

    // Create node map for ID lookup
    const nodeMap = new Map(graphData.nodes.map((node) => [node.id, node]));

    // Convert links to use node references
    const convertedLinks = graphData.links.map((link) => ({
      source: nodeMap.get(link.source),
      target: nodeMap.get(link.target),
    }));

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(convertedLinks)
        .id((d) => d.id)
        .distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Create links
    const link = svg.append("g")
      .selectAll("line")
      .data(convertedLinks)
      .join("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 1.5);

    // Create nodes
    const node = svg.append("g")
      .selectAll("circle")
      .data(graphData.nodes)
      .join("circle")
      .attr("r", (d) => (d.type === "group" ? 20 : 15))
      .attr("fill", (d) => (d.type === "group" ? "#4e79a7" : "#59a14f"))
      .call(
        d3.drag()
          .on("start", dragStarted)
          .on("drag", dragged)
          .on("end", dragEnded)
      );

    // Add labels
    const labels = svg.append("g")
      .selectAll("text")
      .data(graphData.nodes)
      .join("text")
      .text((d) => d.name || d.id)
      .attr("font-size", (d) => (d.type === "group" ? "14px" : "12px"))
      .attr("dx", 15)
      .attr("dy", 5)
      .attr("fill", "#333");

    // Simulation tick handler
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node
        .attr("cx", (d) => (d.x = Math.max(30, Math.min(width - 30, d.x))))
        .attr("cy", (d) => (d.y = Math.max(30, Math.min(height - 30, d.y))));

      labels
        .attr("x", (d) => d.x + 15)
        .attr("y", (d) => d.y + 5);
    });

    // Drag functions
    function dragStarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = Math.max(30, Math.min(width - 30, event.x));
      event.subject.fy = Math.max(30, Math.min(height - 30, event.y));
    }

    function dragEnded(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [graphData]);

  return <svg ref={svgRef} />;
};

export default ForceDirectedGraph;