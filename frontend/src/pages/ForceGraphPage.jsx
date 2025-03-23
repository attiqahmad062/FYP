import React, { useRef, useCallback, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import { Text } from 'three-mesh-ui';

const GraphVisualization3D = () => {
  const fgRef = useRef();
  const dummyData = useMemo(() => ({
    // Your complete dummy data object here
    counts: { /* ... */ },
    data: { /* ... */ },
    status: "success"
  }), []);

  // Generate cyber threat data
  const generateData = useCallback(() => {
    const nodes = [];
    const links = [];

    // Color scheme
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
    dummyData.data.groups.forEach(group => {
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

      // Create relationships
      if (entity.group) {
        links.push({
          source: entity.group,
          target: nodeId,
          type: `${type}-group`
        });
      }

      if (entity.technique) {
        links.push({
          source: nodeId,
          target: entity.technique,
          type: `${type}-technique`
        });
      }

      if (entity.techniques) {
        entity.techniques.forEach(tech => {
          links.push({
            source: nodeId,
            target: tech,
            type: 'software-technique'
          });
        });
      }

      if (entity.groups) {
        entity.groups.forEach(groupId => {
          links.push({
            source: groupId,
            target: nodeId,
            type: 'technique-group'
          });
        });
      }
    };

    // Process all entities
    dummyData.data.campaigns.forEach(c => processEntity(c, 'campaign'));
    dummyData.data.techniques.forEach(t => processEntity(t, 'technique'));
    dummyData.data.softwares.forEach(s => processEntity(s, 'software'));
    dummyData.data.detections.forEach(d => processEntity(d, 'detection'));
    dummyData.data.mitigations.forEach(m => processEntity(m, 'mitigation'));
    dummyData.data.procedures.forEach(p => processEntity(p, 'procedure'));

    // Remove duplicates
    const uniqueNodes = nodes.filter((v,i,a) => 
      a.findIndex(t => t.id === v.id) === i
    );

    return { nodes: uniqueNodes, links };
  }, [dummyData]);

  // Custom 3D node objects
  const nodeThreeObject = useCallback(node => {
    // Create sphere geometry
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(5),
      new THREE.MeshPhongMaterial({
        color: node.color,
        shininess: 100
      })
    );

    // Create text label
    const text = new Text({
      content: `${node.name}\n(${node.type})`,
      fontSize: 0.8,
      backgroundColor: '#333',
      backgroundOpacity: 0.8,
      fontColor: '#fff',
      padding: 0.1,
      textAlign: 'center'
    });
    text.position.z += 8;

    // Add interactivity
    text.userData = { node };
    sphere.userData = { node };

    // Group elements
    const group = new THREE.Group();
    group.add(sphere);
    group.add(text);
    
    return group;
  }, []);

  return (
    <div style={{ height: '100vh', background: '#1a1a1a' }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={generateData()}
        nodeThreeObject={nodeThreeObject}
        linkColor={link => link.color || 'rgba(255,255,255,0.2)'}
        linkWidth={0.5}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={0.5}
        enableNodeDrag={false}
        backgroundColor="#000000"
        showNavInfo={false}
        onEngineStop={() => {
          fgRef.current.cameraPosition({ z: 1000 });
          fgRef.current.controls().autoRotate = true;
          fgRef.current.controls().autoRotateSpeed = 1;
        }}
        onNodeClick={node => {
          // Focus on node when clicked
          fgRef.current.cameraPosition(
            { x: node.x + 100, y: node.y + 100, z: node.z + 100 },
            node,
            3000
          );
        }}
      />
    </div>
  );
};

export default GraphVisualization3D;