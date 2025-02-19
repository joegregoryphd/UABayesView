// Global variables for canvas, context, and dimensions
let width = window.innerWidth;
let height = window.innerHeight;
let scaleFactor = Math.min(width, height) / 800; // Assuming 800 is the baseline dimension for design
let baseLinkDistance = 100; // Base link distance at 800px width
let linkDistance = baseLinkDistance * (Math.min(width, height) / 800); // Scale based on current size

const canvas = d3.select('body').append('canvas')
    .attr('width', width)
    .attr('height', height)
    .node();
const context = canvas.getContext('2d');

// Define simulation globally, initialize empty
let simulation = d3.forceSimulation();

// Update scale factors when the window is resized
function updateScaleFactors() {
    scaleFactor = Math.min(width, height) / 800;
    updatePositions(); // Recalculate positions with new scale factor
}

function updateLinkDistance() {
    linkDistance = baseLinkDistance * (Math.min(width, height) / 800);
    if (simulation) {
        simulation.force('link').distance(linkDistance); // Update the distance dynamically
        simulation.alpha(1).restart();
    }
}

// Listen to window resize events
window.addEventListener('resize', function() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    updateScaleFactors(); // Update scale factors on resize
    updateLinkDistance(); // Update link distances on resize
});

let isSimulationInitialized = false;

// Update node positions based on the canvas size
function updatePositions() {
    simulation.nodes().forEach((node, index, nodes) => {
        const angle = (index / nodes.length) * 2 * Math.PI;
        node.fx = width / 2 + 300 * scaleFactor * Math.cos(angle); // Adjust positioning strategy
        node.fy = height / 2 + 300 * scaleFactor * Math.sin(angle);
    });
    simulation.alpha(1).restart();
}

// Initialize or update the simulation with new data
function initializeSimulation(data) {
    let nodes = data.map((node, index) => ({
        ...node,
        x: width / 2 + 300 * scaleFactor * Math.cos(index / data.length * 2 * Math.PI),
        y: height / 2 + 300 * scaleFactor * Math.sin(index / data.length * 2 * Math.PI),
        id: node.name
    }));

    loadNodePositions(nodes);  // Load saved positions if available

    let links = data.flatMap(d => d.edges.map(edge => ({
        source: nodes.find(n => n.name === edge.from),
        target: nodes.find(n => n.name === edge.to)
    })));

        simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.name).distance(linkDistance).strength(0)) // No link force effect
        .force('charge', d3.forceManyBody().strength(0)) // No repelling or attracting
        .force('x', d3.forceX().strength(0)) // No horizontal force
        .force('y', d3.forceY().strength(0)) // No vertical force
        .on('tick', draw);

        d3.select(canvas).call(d3.drag()
        .container(canvas)
        .subject((event) => simulation.find(event.x, event.y)) 
        .on('start', (event) => dragstarted(event)) // Pass the event parameter to the handler
        .on('drag', (event) => dragged(event)) // Pass the event parameter to the handler
        .on('end', (event) => dragended(event))); // Pass the event parameter to the handler
    
    isSimulationInitialized = true;
}

// Function to draw the canvas
function draw() {
    context.clearRect(0, 0, width, height);
    drawLinks();
    drawNodes();
}

function drawLinks() {
    simulation.force('link').links().forEach(link => {
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const angle = Math.atan2(dy, dx);

        const nodeWidth = 180 * scaleFactor;  // Ensure this is synced with drawNode's sizing
        const nodeHeight = calculateNodeHeight(link.target);  // Make sure calculateNodeHeight accounts for scaling


        const targetDistance = calculateIntersectionDistance(angle, nodeWidth, nodeHeight);
        const shortTargetX = link.target.x - Math.cos(angle) * targetDistance;
        const shortTargetY = link.target.y - Math.sin(angle) * targetDistance;

        context.beginPath();
        context.moveTo(link.source.x, link.source.y);
        context.lineTo(shortTargetX, shortTargetY);
        context.stroke();

        drawArrowhead(context, shortTargetX, shortTargetY, angle);
    });
}

function drawNodes() {
    simulation.nodes().forEach(node => {
        drawNode(context, node);
    });
}

d3.select(canvas).call(d3.drag()
    .container(function() { return this; })
    .subject(function(event, d) {
        return simulation.find(event.x, event.y);
    })
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended));

    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = event.x;
        event.subject.fy = event.y;
        saveNodePositions();  // Call function to save positions whenever a node's position is updated
    }

    function saveNodePositions() {
        const positions = simulation.nodes().map(node => ({ id: node.id, x: node.x, y: node.y }));
        sessionStorage.setItem('nodePositions', JSON.stringify(positions));
    }   
    
    function loadNodePositions(nodes) {
        const storedPositions = JSON.parse(sessionStorage.getItem('nodePositions'));
        if (storedPositions) {
            nodes.forEach(node => {
                const storedNode = storedPositions.find(p => p.id === node.id);
                if (storedNode) {
                    node.x = storedNode.x;
                    node.y = storedNode.y;
                    node.fx = storedNode.x;  // Fix position
                    node.fy = storedNode.y;
                }
            });
        }
    }

function calculateNodeHeight(node) {
    const barHeight = 10;
    const titleHeight = 20;
    const padding = 5;
    const spaceBetweenBars = 5;
    const inferredBarHeight = barHeight * node.inference.length;
    const spaceForBars = spaceBetweenBars * (node.inference.length - 1);
    const textHeight = 14; // Approximate text height
    const spaceForText = padding + textHeight * node.inference.length;
    return titleHeight + inferredBarHeight + spaceForBars + spaceForText + padding * 2;
}

function calculateIntersectionDistance(angle, nodeWidth, nodeHeight) {
    // Calculate the intersection distance based on the angle and node dimensions
    const halfWidth = nodeWidth / 2;
    const halfHeight = nodeHeight / 2;

    // Tan(angle) = Opposite / Adjacent
    // To find where the line intersects the rectangle, we check the width and height separately
    const tanTheta = Math.abs(Math.tan(angle));

    let intersectDist;
    if (tanTheta > halfHeight / halfWidth) {
        // Intersection is at the top/bottom of the rectangle
        intersectDist = halfHeight / Math.abs(Math.sin(angle));
    } else {
        // Intersection is at the sides of the rectangle
        intersectDist = halfWidth / Math.abs(Math.cos(angle));
    }

    return intersectDist;
}


function drawArrowhead(ctx, x, y, theta) {
    const headlen = 15 * scaleFactor; // arrowhead length

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - headlen * Math.cos(theta - Math.PI / 6), y - headlen * Math.sin(theta - Math.PI / 6));
    ctx.lineTo(x - headlen * Math.cos(theta + Math.PI / 6), y - headlen * Math.sin(theta + Math.PI / 6));
    ctx.closePath();
    ctx.fillStyle = 'black';
    ctx.fill();
}

//Wrap text function
function wrapText(context, text, x, y, maxWidth, lineHeight) {
    var words = text.split('_');
    var line = '';

    for(var n = 0; n < words.length; n++) {
        var testLine = line + words[n] + ' ';
        var metrics = context.measureText(testLine);
        var testWidth = metrics.width;
        if (testWidth > maxWidth && n > 0) {
            context.fillText(line, x, y);
            line = words[n] + ' ';
            y += lineHeight;
        } else {
            line = testLine;
        }
    }
    context.fillText(line, x, y);
}

//Count lines function
function countLines(context, text, maxWidth) {
    var words = text.split('_');
    var line = '';
    var lineCount = 1;

    for(var n = 0; n < words.length; n++) {
        var testLine = line + words[n] + ' ';
        var metrics = context.measureText(testLine);
        if (metrics.width > maxWidth && n > 0) {
            line = words[n] + ' ';
            lineCount++;
        } else {
            line = testLine;
        }
    }
    return lineCount;
}

//Draw node function
function drawNode(context, node) {
    const nodeWidth = 180 * scaleFactor; // Width of the node
    const titleHeight = 20 * scaleFactor;
    const barWidth = nodeWidth * 0.6;
    const barHeight = 10 * scaleFactor;
    const padding = 5 * scaleFactor;
    const spaceBetweenBars = 5 * scaleFactor;
    const inferredBarHeight = barHeight * node.inference.length;
    const spaceForBars = spaceBetweenBars * (node.inference.length - 1);
    const textHeight = 13 * scaleFactor; // Approximate text height
    const spaceForText = padding + textHeight * node.inference.length;

    const titleLines = countLines(context, node.name, nodeWidth - 2 * padding);
    const titleBlockHeight = titleHeight * titleLines;
    const nodeHeight = titleBlockHeight + inferredBarHeight + spaceForBars + spaceForText + padding * 2 - 10.5;
    
    const nodeX = node.x - nodeWidth / 2; // Center the node
    const nodeY = node.y - nodeHeight / 2;
    
    // Draw the border of the node
    context.fillStyle = '#fff';
    context.strokeStyle = '#000';
    context.lineWidth = 1;
    context.beginPath();
    context.rect(nodeX, nodeY, nodeWidth, nodeHeight);
    context.fill();
    context.stroke();

    // Draw the title of the node
    context.fillStyle = '#ddd';
    context.fillRect(nodeX, nodeY, nodeWidth, titleBlockHeight);

    // Draw the title text
    context.fillStyle = '#000';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.font = `${textHeight}px Arial`;
    wrapText(context, node.name, nodeX + nodeWidth / 2, nodeY + titleHeight / 2, nodeWidth - 2 * padding, titleHeight);


    // Draw inference bars and text
    node.inference.forEach((value, index) => {
        const barY = nodeY + titleBlockHeight + padding + (barHeight + spaceBetweenBars) * index + padding;
        
        // Draw background bar
        context.fillStyle = '#eee';
        context.fillRect(nodeX + padding, barY, barWidth, barHeight);

        // Draw foreground bar
        context.fillStyle = index % 2 === 0 ? '#F44336':'#4CAF50'; // Alternate colors
        context.fillRect(nodeX + padding, barY, barWidth * (value / 100), barHeight);

        // Draw the inference text
        context.fillStyle = '#000';
        context.textAlign = 'right';
        context.textBaseline = 'middle';
        context.fillText(`${value.toFixed(1)}%`, nodeX + nodeWidth - padding, barY + barHeight / 2);
    });
}

function init(newData) {
    initializeSimulation(newData);
}

function updateData(newData) {
    if (!isSimulationInitialized) {
        initializeSimulation(newData); // Initialize if not already done
    }
    else{
        // Retrieve existing nodes from the simulation
        let nodes = simulation.nodes();

        // Update nodes based on newData
        newData.forEach(newNode => {
            let node = nodes.find(n => n.name === newNode.name);
            if (node) {
                node.inference = newNode.inference;
            }
        });

        // Refresh the simulation to reflect changes and re-render
        simulation.alpha(1).restart(); // Briefly reheat the simulation to adjust visual elements
        draw(); // Redraw the nodes with updated data
    }   
}
