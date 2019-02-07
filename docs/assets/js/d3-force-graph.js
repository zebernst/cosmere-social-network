// RESOURCES:
// https://beta.observablehq.com/@mbostock/disjoint-force-directed-graph
// http://www.puzzlr.org/force-graphs-with-d3/
// https://bl.ocks.org/sjengle/f6f522f3969752b384cfec5449eacd98
// https://bl.ocks.org/heybignick/3faf257bbbbc7743bb72310d03b86ee8
// https://github.com/d3/d3-force

// todo: split simulation off into generalized function that can be included via <script> tag
// todo: add dynamic filters to sort by world, family, profession, etc.

data.then(function (data) {
    const width = window.innerWidth, height = window.innerHeight, radius = 5;
    const filters = {};

    // get master <svg> element
    const svg = d3.select("svg#force-graph")
        .attr("viewBox", [-width/2, -height/2, width, height].join(" "));


    // initialize d3 force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force("charge", d3.forceManyBody()
            .strength(-80))
        .force("links", d3.forceLink(data.links)
            .id(d => d.id)
            .distance(50))
        .force("collide", d3.forceCollide())
        .force("x", d3.forceX())
        .force("y", d3.forceY());

    // define colors
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // create enclosing element for graph data
    const graph = svg.append("g")
        .attr("class", "graph");

    // enable zoom/pan on graph element
    const zoom = d3.zoom()
        .scaleExtent([1/4, 5])
        .on("zoom", () => graph.attr("transform", d3.event.transform));
    svg.call(zoom);

    let link = graph.append("g").attr("class", "links").selectAll("line");
    let node = graph.append("g").attr("class", "nodes").selectAll("circle");
    let label = graph.append("g").attr("class", "labels").selectAll("text");

    // initial drawing with all data
    update(data);

    // add legend
    const legend = svg.append("g")
        .attr("class", "legend")
        .selectAll(".series")
        .data(color.domain())
        .enter()
        .append("g")
        .attr("class", "series")
        .attr("transform", (d, i) => `translate(0, ${20 * i})`)
        .style("cursor", "pointer")
        .on("click", datum => { // apply filter on click
            toggleFilter("world", datum);
            update(subset(data, filters));
        });

    legend.append("circle")
        .attr("r", ".3em")
        .attr("cx", width/2 - (0.025 * width))
        .attr("cy", -height/2 + 50)
        .style("fill", color);
        // todo: format circle as more transparent if series not displayed

    legend.append("text")
        .attr("x", width/2 - (0.025 * width) - 25)
        .attr("y", -height/2 + 50 + 1)
        .attr("dx", 12)
        .style("font-size", ".6em")
        .style("text-anchor", "end")
        .style("alignment-baseline", "middle")
        .text(d => d);
        // todo: format text differently if series is displayed

    const legendTitle = svg.select(".legend")
        .insert("text", ":first-child")
        .attr("x", width/2 - (0.025 * width) + radius)
        .attr("y", -height/2 + 50 + 1)
        .attr("transform", "translate(0, -20)")
        .style("font-size", ".8em")
        .style("text-anchor", "end")
        .text("World");

    function tick() {
        label
            .attr("transform", d => `translate(${d.x}, ${d.y})`)
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
    }
    function drag(simulation) {

        // gentlemen, start your engines!
        function dragStart(d) {
            if (!d3.event.active)
                simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        // good luck, and don't f*ck it up!
        function dragging(d) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
        }

        // now, sashay away
        function dragEnd(d) {
            if (!d3.event.active)
                simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on("start", dragStart)
            .on("drag", dragging)
            .on("end", dragEnd);
    }
    function subset(data, filters) {
        // make sure at least one filter is applied
        const nodes = Object.keys(filters).reduce((numFilters, key) => numFilters + filters[key].size, 0) >= 1
            ? data.nodes.filter(n => Object.keys(n)
                .some(k => {
                    if (filters.hasOwnProperty(k) && filters[k] instanceof Set)
                        return filters[k].has(n[k]);
                    else return false; // return false if filters[k] is not a Set
                }))
            : data.nodes.filter(() => true);
        const links = data.links.filter(l => nodes.includes(l.source) && nodes.includes(l.target));

        return {
            nodes,
            links
        };
    }
    function explicitSubset(data, key, value) {
        const graph = {
            nodes: data.nodes.filter(n => n[key] === value),
            links: data.links.filter(l => graph.nodes.includes(l.source) && graph.nodes.includes(l.target))
        };

        return graph;
    }
    function toggleFilter(key, value) {
        // make sure that key is represented in filters
        if (!filters.hasOwnProperty(key))
            filters[key] = new Set();

        // toggle filter
        if (filters[key].has(value))
            filters[key].delete(value);
        else
            filters[key].add(value);
    }
    function update(data) {
        // update
        link = link.data(data.links, d => d.index);
        node = node.data(data.nodes, d => d.id);
        label = label.data(data.nodes, d => d.id);

        // exit
        link.exit().remove();
        node.exit().remove();
        label.exit().remove();

        // enter + merge
        link = link
            .enter()
            .append("line")
            .attr("stroke-width", 1)
            .attr("stroke-opacity", 0.6)
            .attr("stroke", "#777")
            .merge(link);

        node = node
            .enter()
            .append("circle")
            .attr("r", radius)
            .attr("fill", d => color(d.world))
            .attr("stroke", "#ccc")
            .attr("stroke-width", 1)
            .call(drag(simulation))
            .merge(node);

        label = label
            .enter()
            .append("text")
            .attr("font-size", ".4em")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .attr("pointer-events", "none")
            .attr("user-select", "none")
            .merge(label)
            .text(d => d.id);


        // restart simulation
        simulation.on("tick", tick)
            .nodes(data.nodes)
            .force("links", d3.forceLink(data.links).id(d => d.id).distance(50))
            .alpha(1)
            .alphaTarget(0)
            .restart();
    }
});

