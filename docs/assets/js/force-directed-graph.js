/* ################### *
 * ### d3.js setup ### *
 * ################### */

function forceDirectedGraph() {
    // configurable options
    let width = window.innerWidth,
        height = window.innerHeight,
        radius = 5,
        color = d3.scaleOrdinal(d3.schemeCategory10).unknown('#000');

    // graph state
    const filters = {},
        simulation = d3.forceSimulation()
            .force("charge",
                d3.forceManyBody()
                    .strength(-80))
            .force("links",
                d3.forceLink()
                    .id(d => d.id)
                    .distance(50))
            .force("collide",
                d3.forceCollide())
            .force("x", d3.forceX())
            .force("y", d3.forceY());

    // graph elements
    let link, node, label, legend, legendTitle;

    // d3.js functions
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
    function drag() {

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

    // data manipulation functions
    /** returns a subset of the given data based on the given filter object */
    function subset(data, filters) {
        // make sure at least one filter is applied
        const nodes = Object.keys(filters).reduce((numFilters, key) => numFilters + filters[key].size, 0) >= 1
            ? data.nodes.filter(n => Object.keys(n)
                .some(k => {
                    if (filters.hasOwnProperty(k) && filters[k] instanceof Set)
                        return filters[k].has(n[k]);
                    else return false; // return false if filters[k] is not a Set
                }))
            : data.nodes.filter(() => true); // return all nodes if no filters applied
        const links = data.links.filter(l => nodes.includes(l.source) && nodes.includes(l.target));

        return {
            nodes,
            links
        };
    }
    /** returns a subset of the data based on the explicit key/value given */
    function explicitSubset(data, key, value) {
        const nodes = data.nodes.filter(n => n[key] === value);
        const links = data.links.filter(l => graph.nodes.includes(l.source) && graph.nodes.includes(l.target));

        return {
            nodes,
            links
        };
    }
    /** modifies the graph's filter object to enable/disable the given filter, returns new state */
    function toggleFilter(key, value) {
        // make sure that key is represented in filters
        if (!filters.hasOwnProperty(key))
            filters[key] = new Set();

        // toggle filter
        if (filters[key].has(value)) {
            filters[key].delete(value);
            return false;
        } else {
            filters[key].add(value);
            return true;
        }
    }
    /** returns a boolean representing whether the given filter is present in the global filter object */
    function filterApplied(key, value) {
        return filters.hasOwnProperty(key)
            && filters[key] instanceof Set
            && filters[key].has(value);
    }
    /** populates an array of adjacent neighbors and an array of direct links on each node in the provided data */
    function populateConnections(data) {
        data.links.forEach(function (link) {
            const source = link.source,
                  target = link.target;

            // populate neighbors
            (source.neighbors = source.neighbors || new Set()).add(target);
            (target.neighbors = target.neighbors || new Set()).add(source);

            // populate edges
            (source.edges = source.edges || new Set()).add(link);
            (target.edges = target.edges || new Set()).add(link);
        });

        return data;
    }
    /** returns a subset of the data representing the complete component that contains the given node */
    function component(data, keyNode, nodes=undefined, base=true) {
        nodes = nodes || new Set();

        if (typeof keyNode === 'string' || keyNode instanceof String)
            keyNode = data.nodes.find(n => n.id.toLowerCase() === keyNode.toLowerCase());

        // don't try to iterate over neighbors of invalid node
        if (keyNode) {
            nodes.add(keyNode);

            keyNode.neighbors
                .forEach(n => {
                    if (!nodes.has(n))
                        component(data, n, nodes, false);
            });
        }

        if (base) return {
            nodes: [...nodes],
            links: data.links.filter(l => nodes.has(l.source) && nodes.has(l.target))
        };
    }
    /** returns true if `other` is a node or a link directly connected to `datum`, false otherwise */
    function isConnected(datum, other) {
        return datum.neighbors.has(other)
            || datum.edges.has(other)
            || datum === other;
    }

    // styling functions
    /** fades or highlights nodes and links based on whether or not they're connected to the specified node */
    function fade(fadeOpacity) {
        return function (datum) {
            const opacity = elem => isConnected(datum, elem) ? 1 : fadeOpacity;

            node.style('stroke-opacity', opacity);
            node.style('fill-opacity',   opacity);
            link.style('stroke-opacity', opacity);
        }
    }

    // define draw function
    /** update the graph based on the given data */
    function update(data) {
        const t = d3.transition()
            .duration(300);

        // update
        link = link.data(data.links, d => d.index);
        node = node.data(data.nodes, d => d.id);
        label = label.data(data.nodes, d => d.id);

        // exit
        link.exit()
            .transition(t)
            .attr("stroke-opacity", 0)
            .attrTween("x1", d => () => d.source.x)
            .attrTween("x2", d => () => d.target.x)
            .attrTween("y1", d => () => d.source.y)
            .attrTween("y2", d => () => d.target.y)
            .remove();

        node.exit()
            .transition(t)
            .attr("r", 1e-4)
            .remove();

        label.exit()
            .transition(t)
            .style("opacity", 0)
            .remove();

        // enter + merge
        link = link
            .enter()
            .append("line")
            .classed("link", true)
            .call(l => l.transition(t).attr("stroke-opacity", 1))
            .merge(link);

        node = node
            .enter()
            .append("circle")
            .classed("node", true)
            .style("fill", d => color(d.world))
            .call(drag(simulation))
            .call(n => n.transition(t).attr("r", radius))
            .on('mouseover.highlight', fade(0.2))
            .on('mouseout.highlight', fade(1))
            .merge(node);

        label = label
            .enter()
            .append("text")
            .classed("label", true)
            .attr("dx", 12)
            .attr("dy", ".35em")
            .text(d => d.id)
            .call(l => l.transition(t).style("opacity", 1))
            .merge(label);

        // update legend style for applied filters
        legend
            .select("circle")
            .attr("opacity", d => filterApplied('world', d) ? 1.0 : 0.4);
        legend
            .select("text")
            .style("font-weight", d => filterApplied('world', d) ? "bold" : "normal");


        // restart simulation
        simulation
            .nodes(data.nodes)
            .force("links", d3.forceLink()
                .links(data.links)
                .id(d => d.id)
                .distance(50))
            .alpha(1)
            .alphaTarget(0)
            .on("tick", tick)
            .restart();

        return data;
    }

    // create graph closure
    function graph(selection) {
        selection.each(function (data) {
            const svg = d3.select(this)
                .attr("viewBox", [-width/2, -height/2, width, height].join(" "))
                .call(d3.zoom()
                    .scaleExtent([1/4, 5])
                    .on("zoom", () => graph.attr("transform", d3.event.transform)));

            // clear existing svg elements
            svg.selectAll("*").remove();

            const graph = svg.append("g")
                .classed("graph", true);


            // get elements for data binding
            link = graph.append("g").classed("links", true).selectAll("line");
            node = graph.append("g").classed("nodes", true).selectAll("circle");
            label = graph.append("g").classed("labels", true).selectAll("text");
            legend = svg.append("g").classed("legend", true).selectAll(".series");
            legendTitle = svg.select(".legend").insert("text", ":first-child");

            // initial drawing with all data
            // (transforms links into node references)
            update(data);

            // update nodes with neighbor array (needs to be called after initial update())
            populateConnections(data);

            // add legend
            legend = legend
                .data(color.domain())
                .enter()
                .append("g")
                .classed("series", true)
                .attr("transform", (d, i) => `translate(0, ${20 * i})`)
                .on("click", datum => { // apply filter on click
                    toggleFilter("world", datum);
                    update(subset(data, filters));
                });

            legend
                .append("circle")
                .attr("r", ".3em")
                .attr("cx", width/2 - (0.025 * width))
                .attr("cy", -height/2 + 50)
                .attr("opacity", 0.4) // display filter as disabled initially
                .style("fill", color);

            legend
                .append("text")
                .attr("x", width/2 - (0.025 * width) - 25)
                .attr("y", -height/2 + 50 + 1)
                .attr("dx", 12)
                .style("font-weight", "normal") // display filter as disabled initially
                .text(d => d);

            // add legend title
            legendTitle
                .classed("legend-title", true)
                .attr("x", width/2 - (0.025 * width) + radius)
                .attr("y", -height/2 + 50 + 1)
                .attr("transform", "translate(0, -20)")
                .text("World");
                });
    }

    // define getters/setters
    graph.width = function (value) {
        if (!arguments.length) return width;
        width = value;
        return graph;
    };
    graph.height = function (value) {
        if (!arguments.length) return height;
        height = value;
        return graph;
    };
    graph.radius = function (value) {
        if (!arguments.length) return radius;
        radius = value;
        return graph;
    };
    graph.colorDomain = function (value) {
        if (!arguments.length) return color.domain();
        color.domain(value);
        return graph;
    };
    graph.colorRange = function (value) {
        if (!arguments.length) return color.range();
        color.range(value);
        return graph;
    };

    // expose api for console debugging
    graph.debug = {
        filters,
        subset,
        update,
        component
    };

    return graph;
}