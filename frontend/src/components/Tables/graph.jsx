// import React, { useState, useEffect, useRef, useMemo } from "react";
// import * as d3 from "d3";

// const ForceDirectedGraph = () => {
//   const svgRef = useRef(null);
//   const [graphData, setGraphData] = useState({ nodes: [], links: [] });
//   const [selectedGroup, setSelectedGroup] = useState(null);
//   const [isFullScreen, setIsFullScreen] = useState(false);

//   // Fetch and process data
//   useEffect(() => {
//     const fetchData = async () => {
//       const response = dummyData;

//       const { groups, techniques, software, campaigns, procedures, mitigations, detections, groupConnections } = response;
//       const nodeMap = new Map();
//       const nodes = [];
//       const links = [];

//       // Process groups
//       groups.forEach((group) => {
//         if (!nodeMap.has(group.id)) {
//           const node = { id: group.id, name: group.name, type: "group" };
//           nodes.push(node);
//           nodeMap.set(group.id, node);
//         }
//       });

//       // Process techniques
//       techniques.forEach((technique) => {
//         if (!nodeMap.has(technique.id)) {
//           const node = { id: technique.id, name: technique.name, type: "technique" };
//           nodes.push(node);
//           nodeMap.set(technique.id, node);
//         }
//       });

//       // Process software
//       software.forEach((sw) => {
//         if (!nodeMap.has(sw.id)) {
//           const node = { id: sw.id, name: sw.name, type: "software" };
//           nodes.push(node);
//           nodeMap.set(sw.id, node);
//         }
//       });

//       // Process campaigns
//       campaigns.forEach((campaign) => {
//         if (!nodeMap.has(campaign.id)) {
//           const node = { id: campaign.id, name: campaign.name, type: "campaign" };
//           nodes.push(node);
//           nodeMap.set(campaign.id, node);
//         }
//       });

//       // Process procedures
//       procedures.forEach((procedure) => {
//         if (!nodeMap.has(procedure.id)) {
//           const node = { id: procedure.id, name: procedure.name, type: "procedure", techniqueId: procedure.techniqueId };
//           nodes.push(node);
//           nodeMap.set(procedure.id, node);
//         }
//       });

//       // Process mitigations
//       mitigations.forEach((mitigation) => {
//         if (!nodeMap.has(mitigation.id)) {
//           const node = { id: mitigation.id, name: mitigation.name, type: "mitigation", techniqueId: mitigation.techniqueId };
//           nodes.push(node);
//           nodeMap.set(mitigation.id, node);
//         }
//       });

//       // Process detections
//       detections.forEach((detection) => {
//         if (!nodeMap.has(detection.id)) {
//           const node = { id: detection.id, name: detection.name, type: "detection", techniqueId: detection.techniqueId };
//           nodes.push(node);
//           nodeMap.set(detection.id, node);
//         }
//       });

//       // Process group connections
//  // Process group connections
//     groupConnections.forEach((connection) => {
//       if (connection.techniqueId && nodeMap.has(connection.groupId)) { // Fixed: Added missing parenthesis
//         links.push({ source: connection.groupId, target: connection.techniqueId });
//       }
//       if (connection.softwareId && nodeMap.has(connection.groupId)) {
//         links.push({ source: connection.groupId, target: connection.softwareId });
//       }
//       if (connection.campaignId && nodeMap.has(connection.groupId)) {
//         links.push({ source: connection.groupId, target: connection.campaignId });
//       }
//     });

//       // Process technique connections
//       procedures.forEach((procedure) => {
//         if (nodeMap.has(procedure.techniqueId)) {
//           links.push({ source: procedure.techniqueId, target: procedure.id });
//         }
//       });

//       mitigations.forEach((mitigation) => {
//         if (nodeMap.has(mitigation.techniqueId)) {
//           links.push({ source: mitigation.techniqueId, target: mitigation.id });
//         }
//       });

//       detections.forEach((detection) => {
//         if (nodeMap.has(detection.techniqueId)) {
//           links.push({ source: detection.techniqueId, target: detection.id });
//         }
//       });

//       setGraphData({ nodes, links });
//     };

//     fetchData();
//   }, []);

//   // Compute displayed data based on selection
//   const displayedData = useMemo(() => {
//     if (!graphData.nodes.length) return { nodes: [], links: [] };

//     const groupNodes = graphData.nodes.filter((node) => node.type === "group");

//     if (!selectedGroup) {
//       return { nodes: groupNodes, links: [] };
//     }

//     const selectedLinks = graphData.links.filter(
//       (link) => link.source === selectedGroup
//     );
//     const connectedIds = new Set(selectedLinks.map((link) => link.target));
//     const displayedNodes = graphData.nodes.filter(
//       (node) => node.type === "group" || connectedIds.has(node.id)
//     );

//     return { nodes: displayedNodes, links: selectedLinks };
//   }, [graphData, selectedGroup]);

//   // Render D3 graph
//   useEffect(() => {
//     if (!svgRef.current || displayedData.nodes.length === 0) return;

//     const width = isFullScreen ? window.innerWidth : 1000;
//     const height = isFullScreen ? window.innerHeight : 800;
//     const svg = d3
//       .select(svgRef.current)
//       .html("")
//       .attr("width", width)
//       .attr("height", height)
//       .style("position", isFullScreen ? "fixed" : "relative")
//       .style("top", isFullScreen ? "0" : "auto")
//       .style("left", isFullScreen ? "0" : "auto")
//       .style("z-index", isFullScreen ? "1000" : "auto")
//       .style("background", isFullScreen ? "#fff" : "none");

//     const nodeMap = new Map(displayedData.nodes.map((node) => [node.id, node]));
//     const convertedLinks = displayedData.links.map((link) => ({
//       source: nodeMap.get(link.source),
//       target: nodeMap.get(link.target),
//     }));

//     const simulation = d3
//       .forceSimulation(displayedData.nodes)
//       .force(
//         "link",
//         d3.forceLink(convertedLinks).id((d) => d.id).distance(isFullScreen ? 200 : 100)
//       )
//       .force("charge", d3.forceManyBody().strength(isFullScreen ? -500 : -300))
//       .force("center", d3.forceCenter(width / 2, height / 2))
//       .force("collision", d3.forceCollide().radius(30));

//     const link = svg
//       .append("g")
//       .selectAll("line")
//       .data(convertedLinks)
//       .join("line")
//       .attr("stroke", "#999")
//       .attr("stroke-width", 1.5);

//     const node = svg
//       .append("g")
//       .selectAll("circle")
//       .data(displayedData.nodes)
//       .join("circle")
//       .attr("r", (d) => {
//         if (d.type === "group") return 20;
//         if (d.type === "technique") return 15;
//         if (d.type === "software") return 10;
//         if (d.type === "campaign") return 10;
//         if (d.type === "procedure") return 8;
//         if (d.type === "mitigation") return 8;
//         if (d.type === "detection") return 8;
//         return 5;
//       })
//       .attr("fill", (d) => {
//         if (d.type === "group") return "#4e79a7";
//         if (d.type === "technique") return "#59a14f";
//         if (d.type === "software") return "#f28e2b";
//         if (d.type === "campaign") return "#e15759";
//         if (d.type === "procedure") return "#76b7b2";
//         if (d.type === "mitigation") return "#edc948";
//         if (d.type === "detection") return "#b07aa1";
//         return "#333";
//       })
//       .on("click", (event, d) => {
//         if (d.type === "group") {
//           setSelectedGroup(selectedGroup === d.id ? null : d.id);
//         }
//       })
//       .call(
//         d3
//           .drag()
//           .on("start", (event) => {
//             if (!event.active) simulation.alphaTarget(0.3).restart();
//             event.subject.fx = event.subject.x;
//             event.subject.fy = event.subject.y;
//           })
//           .on("drag", (event) => {
//             event.subject.fx = Math.max(30, Math.min(width - 30, event.x));
//             event.subject.fy = Math.max(30, Math.min(height - 30, event.y));
//           })
//           .on("end", (event) => {
//             if (!event.active) simulation.alphaTarget(0);
//             event.subject.fx = null;
//             event.subject.fy = null;
//           })
//       );

//     const labels = svg
//       .append("g")
//       .selectAll("text")
//       .data(displayedData.nodes)
//       .join("text")
//       .text((d) => d.name || d.id)
//       .attr("font-size", (d) => {
//         if (d.type === "group") return "14px";
//         if (d.type === "technique") return "12px";
//         return "10px";
//       })
//       .attr("dx", 15)
//       .attr("dy", 5)
//       .attr("fill", "#333");

//     simulation.on("tick", () => {
//       link
//         .attr("x1", (d) => d.source.x)
//         .attr("y1", (d) => d.source.y)
//         .attr("x2", (d) => d.target.x)
//         .attr("y2", (d) => d.target.y);

//       node
//         .attr("cx", (d) => (d.x = Math.max(30, Math.min(width - 30, d.x))))
//         .attr("cy", (d) => (d.y = Math.max(30, Math.min(height - 30, d.y))));

//       labels.attr("x", (d) => d.x + 15).attr("y", (d) => d.y + 5);
//     });

//     return () => simulation.stop();
//   }, [displayedData, isFullScreen]);

//   return (
//     <div style={{ position: "relative" }}>
//       <button
//         onClick={() => setIsFullScreen(!isFullScreen)}
//         style={{
//           position: "absolute",
//           top: "10px",
//           right: "10px",
//           zIndex: 1001,
//           padding: "5px 10px",
//           cursor: "pointer",
//         }}
//       >
//         {isFullScreen ? "Exit Full Screen" : "Full Screen"}
//       </button>
//       <svg ref={svgRef}></svg>
//     </div>
//   );
// };

// export default ForceDirectedGraph;



import React, { useState, useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";

const ForceDirectedGraph = () => {
  const svgRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Fetch and process data
  useEffect(() => {
    const fetchData = async () => {
      const response = {
        counts: { groups: 10, techniques: 12 },
        data: {
          groups: [
            { id: "G0018", name: "admin@338" },
            { id: "G0018", name: "PoisonIvy" },
            { id: "G0130", name: "Ajax Security Team" },
            { id: "G0130", name: "Ajax_Security_Team" },
            { id: "G1024", name: "Akira" },
            { id: "G1000", name: "ALLANITE" },
            { id: "G1000", name: "ICS" },
            { id: "G0138", name: "Lazarus Group" },
            { id: "G0138", name: "Andariel" },
            { id: "G1007", name: "Aoqin_Dragon" },
          ],
          techniques: [
            { groups: ["G0018"], id: "T1087" },
            { groups: ["G0016"], id: "T1087" },
            { groups: ["G0130"], id: "T1087" },
            { groups: ["G0050"], id: "T1087" },
            { groups: ["G1024"], id: "T1037" },
            { groups: ["G1024"], id: "T1187" },
            { groups: ["G1024"], id: "T1287" },
            { groups: ["G1016"], id: "T1487" },
            { groups: ["G0138"], id: "T1287" },
            { groups: ["G0138"], id: "T10" },
            { groups: ["G0138"], id: "T1087" },
            { groups: ["G0045"], id: "T3087" },
          ],
        },
        status: "success",
      };

      const { groups, techniques } = response.data;
      const nodeMap = new Map();
      const nodes = [];
      const links = [];

      // Process groups (use first name for duplicate IDs)
      groups.forEach((group) => {
        if (!nodeMap.has(group.id)) {
          const node = { id: group.id, name: group.name, type: "group" };
          nodes.push(node);
          nodeMap.set(group.id, node);
        }
      });

      // Process techniques and create links
      techniques.forEach((technique) => {
        const techId = technique.id;
        if (!nodeMap.has(techId)) {
          const node = { id: techId, type: "technique" };
          nodes.push(node);
          nodeMap.set(techId, node);
        }
        technique.groups.forEach((groupId) => {
          if (nodeMap.has(groupId)) {
            links.push({ source: groupId, target: techId });
          }
        });
      });

      setGraphData({ nodes, links });
    };

    fetchData();
  }, []);

  // Compute displayed data based on selection
  const displayedData = useMemo(() => {
    if (!graphData.nodes.length) return { nodes: [], links: [] };

    const groupNodes = graphData.nodes.filter((node) => node.type === "group");

    if (!selectedGroup) {
      return { nodes: groupNodes, links: [] };
    }

    const selectedLinks = graphData.links.filter(
      (link) => link.source === selectedGroup
    );
    const techniqueIds = new Set(selectedLinks.map((link) => link.target));
    const displayedTechniques = graphData.nodes.filter(
      (node) => node.type === "technique" && techniqueIds.has(node.id)
    );
    const displayedNodes = [...groupNodes, ...displayedTechniques];

    return { nodes: displayedNodes, links: selectedLinks };
  }, [graphData, selectedGroup]);

  // Render D3 graph
  useEffect(() => {
    if (!svgRef.current || displayedData.nodes.length === 0) return;

    const width = isFullScreen ? window.innerWidth : 1000;
    const height = isFullScreen ? window.innerHeight : 800;
    const svg = d3
      .select(svgRef.current)
      .html("")
      .attr("width", width)
      .attr("height", height)
      .style("position", isFullScreen ? "fixed" : "relative")
      .style("top", isFullScreen ? "0" : "auto")
      .style("left", isFullScreen ? "0" : "auto")
      .style("z-index", isFullScreen ? "1000" : "auto")
      .style("background", isFullScreen ? "#fff" : "none");

    const nodeMap = new Map(displayedData.nodes.map((node) => [node.id, node]));
    const convertedLinks = displayedData.links.map((link) => ({
      source: nodeMap.get(link.source),
      target: nodeMap.get(link.target),
    }));

    const simulation = d3
      .forceSimulation(displayedData.nodes)
      .force(
        "link",
        d3.forceLink(convertedLinks).id((d) => d.id).distance(isFullScreen ? 200 : 100)
      )
      .force("charge", d3.forceManyBody().strength(isFullScreen ? -500 : -300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(convertedLinks)
      .join("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 1.5);

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(displayedData.nodes)
      .join("circle")
      .attr("r", (d) => (d.type === "group" ? 20 : 15))
      .attr("fill", (d) => (d.type === "group" ? "#4e79a7" : "#59a14f"))
      .on("click", (event, d) => {
        if (d.type === "group") {
          setSelectedGroup(selectedGroup === d.id ? null : d.id);
        }
      })
      .call(
        d3
          .drag()
          .on("start", (event) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
          })
          .on("drag", (event) => {
            event.subject.fx = Math.max(30, Math.min(width - 30, event.x));
            event.subject.fy = Math.max(30, Math.min(height - 30, event.y));
          })
          .on("end", (event) => {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
          })
      );

    const labels = svg
      .append("g")
      .selectAll("text")
      .data(displayedData.nodes)
      .join("text")
      .text((d) => d.name || d.id)
      .attr("font-size", (d) => (d.type === "group" ? "14px" : "12px"))
      .attr("dx", 15)
      .attr("dy", 5)
      .attr("fill", "#333");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node
        .attr("cx", (d) => (d.x = Math.max(30, Math.min(width - 30, d.x))))
        .attr("cy", (d) => (d.y = Math.max(30, Math.min(height - 30, d.y))));

      labels.attr("x", (d) => d.x + 15).attr("y", (d) => d.y + 5);
    });

    return () => simulation.stop();
  }, [displayedData, isFullScreen]);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setIsFullScreen(!isFullScreen)}
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
          zIndex: 1001,
          padding: "5px 10px",
          cursor: "pointer",
        }}
      >
        {isFullScreen ? "Exit Full Screen" : "Full Screen"}
      </button>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default ForceDirectedGraph;