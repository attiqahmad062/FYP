// import React, { useRef, useCallback, useMemo } from 'react';
// import ForceGraph3D from 'react-force-graph-3d';
// import * as THREE from 'three';
// import { Text } from 'three-mesh-ui';

// const GraphVisualization3D = () => {
//   const fgRef = useRef();
//   const dummyData = useMemo(() => ({
//     // Your complete dummy data object here
//     counts: { /* ... */ },
//     data: { /* ... */ },
//     status: "success"
//   }), []);

//   // Generate cyber threat data
//   const generateData = useCallback(() => {
//     const nodes = [];
//     const links = [];

//     // Color scheme
//     const typeColors = {
//       group: '#FF6B6B',
//       campaign: '#4ECDC4',
//       technique: '#45B7D1',
//       software: '#96CEB4',
//       detection: '#FFEEAD',
//       mitigation: '#D4A5A5',
//       procedure: '#88B04B'
//     };

//     // Add Groups
//     dummyData.data.groups.forEach(group => {
//       nodes.push({
//         id: group.id,
//         name: group.name,
//         type: 'group',
//         description: group.description,
//         color: typeColors.group
//       });
//     });

//     // Process Entities
//     const processEntity = (entity, type) => {
//       const nodeId = entity.id || entity.name;
      
//       nodes.push({
//         id: nodeId,
//         name: entity.name,
//         type,
//         description: entity.description || `${type}: ${entity.name}`,
//         color: typeColors[type]
//       });

//       // Create relationships
//       if (entity.group) {
//         links.push({
//           source: entity.group,
//           target: nodeId,
//           type: `${type}-group`
//         });
//       }

//       if (entity.technique) {
//         links.push({
//           source: nodeId,
//           target: entity.technique,
//           type: `${type}-technique`
//         });
//       }

//       if (entity.techniques) {
//         entity.techniques.forEach(tech => {
//           links.push({
//             source: nodeId,
//             target: tech,
//             type: 'software-technique'
//           });
//         });
//       }

//       if (entity.groups) {
//         entity.groups.forEach(groupId => {
//           links.push({
//             source: groupId,
//             target: nodeId,
//             type: 'technique-group'
//           });
//         });
//       }
//     };

//     // Process all entities
//     dummyData.data.campaigns.forEach(c => processEntity(c, 'campaign'));
//     dummyData.data.techniques.forEach(t => processEntity(t, 'technique'));
//     dummyData.data.softwares.forEach(s => processEntity(s, 'software'));
//     dummyData.data.detections.forEach(d => processEntity(d, 'detection'));
//     dummyData.data.mitigations.forEach(m => processEntity(m, 'mitigation'));
//     dummyData.data.procedures.forEach(p => processEntity(p, 'procedure'));

//     // Remove duplicates
//     const uniqueNodes = nodes.filter((v,i,a) => 
//       a.findIndex(t => t.id === v.id) === i
//     );

//     return { nodes: uniqueNodes, links };
//   }, [dummyData]);

//   // Custom 3D node objects
//   const nodeThreeObject = useCallback(node => {
//     // Create sphere geometry
//     const sphere = new THREE.Mesh(
//       new THREE.SphereGeometry(5),
//       new THREE.MeshPhongMaterial({
//         color: node.color,
//         shininess: 100
//       })
//     );

//     // Create text label
//     const text = new Text({
//       content: `${node.name}\n(${node.type})`,
//       fontSize: 0.8,
//       backgroundColor: '#333',
//       backgroundOpacity: 0.8,
//       fontColor: '#fff',
//       padding: 0.1,
//       textAlign: 'center'
//     });
//     text.position.z += 8;

//     // Add interactivity
//     text.userData = { node };
//     sphere.userData = { node };

//     // Group elements
//     const group = new THREE.Group();
//     group.add(sphere);
//     group.add(text);
    
//     return group;
//   }, []);

//   return (
//     <div style={{ height: '100vh', background: '#1a1a1a' }}>
//       <ForceGraph3D
//         ref={fgRef}
//         graphData={generateData()}
//         nodeThreeObject={nodeThreeObject}
//         linkColor={link => link.color || 'rgba(255,255,255,0.2)'}
//         linkWidth={0.5}
//         linkDirectionalArrowLength={3}
//         linkDirectionalArrowRelPos={0.5}
//         enableNodeDrag={false}
//         backgroundColor="#000000"
//         showNavInfo={false}
//         onEngineStop={() => {
//           fgRef.current.cameraPosition({ z: 1000 });
//           fgRef.current.controls().autoRotate = true;
//           fgRef.current.controls().autoRotateSpeed = 1;
//         }}
//         onNodeClick={node => {
//           // Focus on node when clicked
//           fgRef.current.cameraPosition(
//             { x: node.x + 100, y: node.y + 100, z: node.z + 100 },
//             node,
//             3000
//           );
//         }}
//       />
//     </div>
//   );
// };

// export default GraphVisualization3D;


// import React, { useRef, useCallback, useMemo, useState, useEffect } from 'react';
// import ForceGraph3D from 'react-force-graph-3d';
// import * as THREE from 'three';
// // Remove three-mesh-ui and use SpriteText instead
// import SpriteText from 'three-spritetext';

// const GraphVisualization3D = () => {
//   const fgRef = useRef();
//   const [graphData, setGraphData] = useState({ nodes: [], links: [] });

//   const [hoveredNode, setHoveredNode] = useState(null);
//   const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
//   // Complete dummy data - make sure this is properly populated
//   const dummyData = useMemo(() => ({
//     counts: {
//       campaigns: 10,
//       detections: 10,
//       groups: 10,
//       mitigations: 10,
//       procedures: 10,
//       softwares: 10,
//       techniques: 10
//     },
//     data: {
//       campaigns: [
//         { id: "C0031", group: "G1027", name: "Unitronics Defacement Campaign", firstSeen: "2023-11-01", lastSeen: "2023-11-01" },
//         { id: "C0033", group: "G0056", name: "Operation Ghost", firstSeen: "2016-05-01", lastSeen: "2023-01-01" },
//         { id: "C0011", group: "G0134", name: "Phishing Campaign", firstSeen: "2021-12-01", lastSeen: "2022-07-01" },
//         { id: "C0023", group: "G0016", name: "Data Exfiltration", firstSeen: "2013-09-01", lastSeen: "2019-10-01" },
//         { id: "C0027", group: "G1015", name: "Ransomware Deployment", firstSeen: "2022-06-01", lastSeen: "2022-12-01" },
//         { id: "C0032", group: "G0099", name: "Supply Chain Attack", firstSeen: "2014-10-01", lastSeen: "2017-01-01" },
//         { id: "C0045", group: "G0138", name: "Cryptojacking", firstSeen: "2020-03-01", lastSeen: "2023-05-01" },
//         { id: "C0056", group: "G1000", name: "ICS Targeting", firstSeen: "2018-11-01", lastSeen: "2022-09-01" },
//         { id: "C0067", group: "G1024", name: "Double Extortion", firstSeen: "2023-03-01", lastSeen: "2023-11-01" },
//         { id: "C0089", group: "G0130", name: "Espionage Campaign", firstSeen: "2015-07-01", lastSeen: "2021-02-01" }
//       ],
//       groups: [
//         { id: "G1027", name: "Industrial Spy", description: "Targets critical infrastructure" },
//         { id: "G0056", name: "Ghost Collective", description: "Advanced persistent threat group" },
//         { id: "G0134", name: "Phish Masters", description: "Specializes in social engineering" },
//         { id: "G0016", name: "Data Snatchers", description: "Focuses on data exfiltration" },
//         { id: "G1015", name: "Ransom Lords", description: "Ransomware-as-a-service operators" },
//         { id: "G0099", name: "Supply Chain Breakers", description: "Compromises software dependencies" },
//         { id: "G0138", name: "Crypto Miners", description: "Illicit cryptocurrency operations" },
//         { id: "G1000", name: "ICS Invaders", description: "Industrial control system specialists" },
//         { id: "G1024", name: "Double Trouble", description: "Dual ransomware/extortion attacks" },
//         { id: "G0130", name: "Covert Eyes", description: "Cyber espionage operations" }
//       ],
//       techniques: [
//         { id: "T1056", groups: ["G1027", "G0056"], name: "Input Capture" },
//         { id: "T1560", groups: ["G0134", "G0016"], name: "Archive Collected Data" },
//         { id: "T1218", groups: ["G1015", "G0099"], name: "Signed Binary Proxy Execution" },
//         { id: "T1585", groups: ["G0138", "G1000"], name: "Phishing for Information" },
//         { id: "T1090", groups: ["G1024", "G0130"], name: "Network Proxy" },
//         { id: "T1656", groups: ["G1027", "G0134"], name: "Impersonation" },
//         { id: "T1047", groups: ["G0016", "G1015"], name: "Windows Management Instrumentation" },
//         { id: "T1027", groups: ["G0099", "G0138"], name: "Obfuscated Files or Information" },
//         { id: "T1547", groups: ["G1000", "G1024"], name: "Boot or Logon Autostart Execution" },
//         { id: "T1071", groups: ["G0130", "G0056"], name: "Application Layer Protocol" }
//       ],
//       detections: [
//         { id: "DS0024", technique: "T1056", dataSource: "Windows Registry", detects: "Credential material changes" },
//         { id: "DS0033", technique: "T1560", dataSource: "Network Traffic", detects: "Unusual data compression patterns" },
//         { id: "DS0045", technique: "T1218", dataSource: "Process Monitoring", detects: "Suspicious binary execution" },
//         { id: "DS0067", technique: "T1585", dataSource: "Email Gateway", detects: "Phishing email patterns" },
//         { id: "DS0089", technique: "T1090", dataSource: "Network Protocols", detects: "Proxy server anomalies" },
//         { id: "DS0012", technique: "T1656", dataSource: "User Account Management", detects: "Account impersonation attempts" },
//         { id: "DS0056", technique: "T1047", dataSource: "WMI Logs", detects: "Suspicious WMI commands" },
//         { id: "DS0078", technique: "T1027", dataSource: "File Analysis", detects: "Obfuscated file artifacts" },
//         { id: "DS0099", technique: "T1547", dataSource: "Boot Records", detects: "Unauthorized startup items" },
//         { id: "DS0034", technique: "T1071", dataSource: "Network Protocols", detects: "Unusual application layer traffic" }
//       ],
//       mitigations: [
//         { id: "M1047", technique: "T1056", name: "Credential Guard", description: "Implement credential protection mechanisms" },
//         { id: "M2056", technique: "T1560", name: "Data Loss Prevention", description: "Monitor data compression activities" },
//         { id: "M3089", technique: "T1218", name: "Binary Allowlisting", description: "Restrict unsigned binary execution" },
//         { id: "M4021", technique: "T1585", name: "Email Filtering", description: "Implement advanced phishing detection" },
//         { id: "M5078", technique: "T1090", name: "Network Segmentation", description: "Monitor proxy server traffic" },
//         { id: "M6090", technique: "T1656", name: "MFA Enforcement", description: "Implement multi-factor authentication" },
//         { id: "M7045", technique: "T1047", name: "WMI Auditing", description: "Log and monitor WMI activity" },
//         { id: "M8012", technique: "T1027", name: "File Analysis", description: "Implement file integrity monitoring" },
//         { id: "M9067", technique: "T1547", name: "Secure Boot", description: "Maintain secure boot configurations" },
//         { id: "M1001", technique: "T1071", name: "Protocol Inspection", description: "Analyze application layer protocols" }
//       ],
//       procedures: [
//         { name: "Credential Theft", technique: "T1056", description: "Using input capture for credential harvesting" },
//         { name: "Data Compression", technique: "T1560", description: "Using custom compression algorithms" },
//         { name: "Binary Proxy", technique: "T1218", description: "Abusing trusted binaries for execution" },
//         { name: "Spear Phishing", technique: "T1585", description: "Targeted email compromise attempts" },
//         { name: "Proxy Chains", technique: "T1090", description: "Multi-hop proxy network setup" },
//         { name: "Account Takeover", technique: "T1656", description: "Impersonating legitimate users" },
//         { name: "WMI Abuse", technique: "T1047", description: "Using WMI for lateral movement" },
//         { name: "File Obfuscation", technique: "T1027", description: "Hiding malicious payloads in files" },
//         { name: "Persistence Mechanism", technique: "T1547", description: "Registry modifications for persistence" },
//         { name: "Protocol Tunneling", technique: "T1071", description: "Tunneling traffic through allowed protocols" }
//       ],
//       softwares: [
//         { id: "S0013", group: "G1027", name: "ShadowRAT", techniques: ["T1056", "T1218"] },
//         { id: "S0045", group: "G0056", name: "GhostLoader", techniques: ["T1560", "T1547"] },
//         { id: "S0067", group: "G0134", name: "PhishKit", techniques: ["T1585", "T1656"] },
//         { id: "S0089", group: "G0016", name: "DataGrabber", techniques: ["T1090", "T1071"] },
//         { id: "S0021", group: "G1015", name: "RansomX", techniques: ["T1027", "T1047"] },
//         { id: "S0034", group: "G0099", name: "DependencyHijack", techniques: ["T1218", "T1560"] },
//         { id: "S0056", group: "G0138", name: "CryptoMiner", techniques: ["T1547", "T1056"] },
//         { id: "S0078", group: "G1000", name: "ICSController", techniques: ["T1071", "T1090"] },
//         { id: "S0099", group: "G1024", name: "DoubleLock", techniques: ["T1585", "T1656"] },
//         { id: "S0012", group: "G0130", name: "SilentObserver", techniques: ["T1047", "T1027"] }
//       ]
//     },
//     status: "success"
//   }), []);

//   // Generate cyber threat data

//   useEffect(() => {
//     const generateData = () => {
//       const nodes = [];
//       const links = [];
//       const typeColors = {
//         group: '#FF6B6B',
//         campaign: '#4ECDC4',
//         technique: '#45B7D1',
//         software: '#96CEB4',
//         detection: '#FFEEAD',
//         mitigation: '#D4A5A5',
//         procedure: '#88B04B'
//       };

//       // Add Groups
//       dummyData.data.groups.forEach(group => {
//         nodes.push({
//           id: group.id,
//           name: group.name,
//           type: 'group',
//           description: group.description,
//           color: typeColors.group
//         });
//       });

//       // Process Entities
//       const processEntity = (entity, type) => {
//         const nodeId = entity.id || entity.name;
        
//         nodes.push({
//           id: nodeId,
//           name: entity.name,
//           type,
//           description: entity.description || `${type}: ${entity.name}`,
//           color: typeColors[type]
//         });

//         // Relationships
//         if (entity.group) {
//           links.push({ source: entity.group, target: nodeId });
//         }
//         if (entity.technique) {
//           links.push({ source: nodeId, target: entity.technique });
//         }
//         if (entity.techniques) {
//           entity.techniques.forEach(tech => {
//             links.push({ source: nodeId, target: tech });
//           });
//         }
//         if (entity.groups) {
//           entity.groups.forEach(groupId => {
//             links.push({ source: groupId, target: nodeId });
//           });
//         }
//       };

//       // Process all entities
//       dummyData.data.campaigns.forEach(c => processEntity(c, 'campaign'));
//       dummyData.data.techniques.forEach(t => processEntity(t, 'technique'));
//       dummyData.data.softwares.forEach(s => processEntity(s, 'software'));
//       dummyData.data.detections.forEach(d => processEntity(d, 'detection'));
//       dummyData.data.mitigations.forEach(m => processEntity(m, 'mitigation'));
//       dummyData.data.procedures.forEach(p => processEntity(p, 'procedure'));

//       // Remove duplicates
//       const uniqueNodes = nodes.filter((v,i,a) => 
//         a.findIndex(t => t.id === v.id) === i
//       );

//       setGraphData({ nodes: uniqueNodes, links });
//     };

//     generateData();
//   }, [dummyData]);
//   // Custom 3D node objects using SpriteText
//   const nodeThreeObject = useCallback(node => {
//     // Create sphere
//     const sphere = new THREE.Mesh(
//       new THREE.SphereGeometry(8),
//       new THREE.MeshPhongMaterial({
//         color: node.color,
//         shininess: 100,
//         transparent: true,
//         opacity: 0.8
//       })
//     );

//     // Create text sprite
//     const text = new SpriteText(`${node.name}\n(${node.type})`);
//     text.color = '#ffffff';
//     text.backgroundColor = '#000000';
//     text.textHeight = 4;
//     text.position.z = 15;

//     // Group elements
//     const group = new THREE.Group();
//     group.add(sphere);
//     group.add(text);
    
//     return group;
//   }, []);

//   return (
//     <div style={{ height: '100vh', background: '#1a1a1a' }}>
//     <ForceGraph3D
//       ref={fgRef}
//       graphData={graphData}
//       nodeThreeObject={node => {
//         const geometry = new THREE.SphereGeometry(4);
//         const material = new THREE.MeshPhongMaterial({ 
//           color: node.color,
//           shininess: 50,
//           transparent: true,
//           opacity: 0.9
//         });
//         return new THREE.Mesh(geometry, material);
//       }}
//       linkDirectionalArrowLength={6}
//       linkDirectionalArrowRelPos={0.8}
//       linkDirectionalArrowColor={() => 'rgba(100,100,255,0.8)'}
//       linkColor={() => 'rgba(100,100,255,0.6)'}
//       linkWidth={1}
//       enableNodeDrag={true}
//       backgroundColor="#0a0a0a"
//       showNavInfo={true}
//       onEngineStop={() => {
//         fgRef.current.cameraPosition({ z: 400 });
//         fgRef.current.controls().autoRotate = true;
//         fgRef.current.controls().autoRotateSpeed = 1.5;
//       }}
//       onNodeHover={node => setHoveredNode(node)}
//       onRenderFramePost={() => {
//         if (hoveredNode) {
//           const { x, y } = fgRef.current.graph2ScreenCoords(
//             hoveredNode.x,
//             hoveredNode.y,
//             hoveredNode.z
//           );
//           setTooltipPos({ x, y });
//         }
//       }}
//       onNodeClick={node => {
//         fgRef.current.cameraPosition(
//           { x: node.x * 1.3, y: node.y * 1.3, z: node.z * 1.3 },
//           node,
//           800
//         );
//       }}
//     />

//     {/* Tooltip */}
//     <div
//       style={{
//         position: 'fixed',
//         display: hoveredNode ? 'block' : 'none',
//         left: tooltipPos.x,
//         top: tooltipPos.y,
//         background: 'rgba(0,0,0,0.8)',
//         color: '#fff',
//         padding: '4px 8px',
//         borderRadius: '4px',
//         pointerEvents: 'none',
//         transform: 'translate(-50%, calc(-100% - 10px)'
//       }}
//     >
//       {hoveredNode && (
//         <>
//           <div>{hoveredNode.name}</div>
//           <div style={{ fontSize: '0.8em', color: '#ccc' }}>
//             {hoveredNode.type}
//           </div>
//         </>
//       )}
//     </div>
//   </div>
//   );
// };

// export default GraphVisualization3D;

import React, { useRef, useCallback, useMemo, useState, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
// Remove three-mesh-ui and use SpriteText instead
import SpriteText from 'three-spritetext';

const GraphVisualization3D = () => {
  const fgRef = useRef();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dataEntries, setDataEntries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  // Complete dummy data - make sure this is properly populated
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5001/all-entries');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDataEntries(data);
        setGraphData(generateData(data.data)); // Use existing generateData function
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);
  

  // Generate cyber threat data

  
    const generateData = (apiData) => {
      const nodes = [];
      const links = [];
      const typeColors = {
        group: '#FF6B6B',
        campaign: '#4ECDC4',
        technique: '#45B7D1',
        software: '#96CEB4',
        detection: '#FFEEAD',
        mitigation: '#D4A5A5',
        procedure: '#88B04B'
      };

      // Add Groups
      apiData.groups.forEach(group => {
        nodes.push({
          id: group.id,
          name: group.name,
          type: 'group',
          description: group.description,
          color: typeColors.group
        });
      });

      // Process Entities
      const processEntity = (entity, type) => {
        const nodeId = entity.id || entity.name;
        
        nodes.push({
          id: nodeId,
          name: entity.name,
          type,
          description: entity.description || `${type}: ${entity.name}`,
          color: typeColors[type]
        });

        // Relationships
        if (entity.group) {
          links.push({ source: entity.group, target: nodeId });
        }
        if (entity.technique) {
          links.push({ source: nodeId, target: entity.technique });
        }
        if (entity.techniques) {
          entity.techniques.forEach(tech => {
            links.push({ source: nodeId, target: tech });
          });
        }
        if (entity.groups) {
          entity.groups.forEach(groupId => {
            links.push({ source: groupId, target: nodeId });
          });
        }
      };

      // Process all entities
      apiData.campaigns.forEach(c => processEntity(c, 'campaign'));
      apiData.techniques.forEach(t => processEntity(t, 'technique'));
      apiData.softwares.forEach(s => processEntity(s, 'software'));
      apiData.detections.forEach(d => processEntity(d, 'detection'));
      apiData.mitigations.forEach(m => processEntity(m, 'mitigation'));
      apiData.procedures.forEach(p => processEntity(p, 'procedure'));

      // Remove duplicates
      const uniqueNodes = nodes.filter((v,i,a) => 
        a.findIndex(t => t.id === v.id) === i
      );

      // setGraphData({ nodes: uniqueNodes, links });
      return { nodes: uniqueNodes, links };
    };

   
    
  
  // Custom 3D node objects using SpriteText
  const nodeThreeObject = useCallback(node => {
    // Create sphere
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(8),
      new THREE.MeshPhongMaterial({
        color: node.color,
        shininess: 100,
        transparent: true,
        opacity: 0.8
      })
    );

    // Create text sprite
    const text = new SpriteText(`${node.name}\n(${node.type})`);
    text.color = '#ffffff';
    text.backgroundColor = '#000000';
    text.textHeight = 4;
    text.position.z = 15;

    // Group elements
    const group = new THREE.Group();
    group.add(sphere);
    group.add(text);
    
    return group;
  }, []);
  if (loading) return <div>Loading threat intelligence data...</div>;
  if (error) return <div>Error: {error}</div>;
  return (
    <div style={{ height: '100vh', background: '#1a1a1a' }}>
    <ForceGraph3D
      ref={fgRef}
      graphData={graphData}
      nodeThreeObject={node => {
        const geometry = new THREE.SphereGeometry(4);
        const material = new THREE.MeshPhongMaterial({ 
          color: node.color,
          shininess: 50,
          transparent: true,
          opacity: 0.9
        });
        return new THREE.Mesh(geometry, material);
      }}
      linkDirectionalArrowLength={6}
      linkDirectionalArrowRelPos={0.8}
      linkDirectionalArrowColor={() => 'rgba(100,100,255,0.8)'}
      linkColor={() => 'rgba(100,100,255,0.6)'}
      linkWidth={1}
      enableNodeDrag={true}
      backgroundColor="#0a0a0a"
      showNavInfo={true}
      onEngineStop={() => {
        fgRef.current.cameraPosition({ z: 400 });
        fgRef.current.controls().autoRotate = true;
        fgRef.current.controls().autoRotateSpeed = 1.5;
      }}
      onNodeHover={node => setHoveredNode(node)}
      onRenderFramePost={() => {
        if (hoveredNode) {
          const { x, y } = fgRef.current.graph2ScreenCoords(
            hoveredNode.x,
            hoveredNode.y,
            hoveredNode.z
          );
          setTooltipPos({ x, y });
        }
      }}
      onNodeClick={node => {
        fgRef.current.cameraPosition(
          { x: node.x * 1.3, y: node.y * 1.3, z: node.z * 1.3 },
          node,
          800
        );
      }}
    />

    {/* Tooltip */}
    <div
      style={{
        position: 'fixed',
        display: hoveredNode ? 'block' : 'none',
        left: tooltipPos.x,
        top: tooltipPos.y,
        background: 'rgba(0,0,0,0.8)',
        color: '#fff',
        padding: '4px 8px',
        borderRadius: '4px',
        pointerEvents: 'none',
        transform: 'translate(-50%, calc(-100% - 10px)'
      }}
    >
      {hoveredNode && (
        <>
          <div>{hoveredNode.name}</div>
          <div style={{ fontSize: '0.8em', color: '#ccc' }}>
            {hoveredNode.type}
          </div>
        </>
      )}
    </div>
  </div>
  );
  };

export default GraphVisualization3D;