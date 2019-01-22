---
title: Family
permalink: /family
layout: default
---

<svg id="force-graph"></svg>
<script src="https://d3js.org/d3.v5.min.js"></script>
<script lang="text/javascript">
    // RESOURCES:
    // https://beta.observablehq.com/@mbostock/disjoint-force-directed-graph
    // http://www.puzzlr.org/force-graphs-with-d3/
    // https://bl.ocks.org/sjengle/f6f522f3969752b384cfec5449eacd98
    // https://bl.ocks.org/heybignick/3faf257bbbbc7743bb72310d03b86ee8
    // https://github.com/d3/d3-force

    // todo: split simulation off into generalized function that can be included via <script> tag

    const data_url = "https://raw.githubusercontent.com/zebernst/cosmere-social-network/master/data/networks/json/family.json";
    d3.json(data_url).then(function (data) {

        const width = 600, height = 600;

        // get master <svg> element
        const svg = d3.select("svg#force-graph")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-width/2, -height/2, width, height].join(" "));

        // initialize d3 force simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force("charge", d3.forceManyBody())
            .force("links", d3.forceLink(data.links).id(d => d.id))
            .force("x", d3.forceX())
            .force("y", d3.forceY());

        // define drag functions
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

        // add links between nodes first
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(data.links)
            .enter()
            .append("line")
            .attr("stroke-width", 2)
            .attr("stroke-opacity", 0.6)
            .attr("stroke", "#777");

        // add nodes on top
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("r", 5)
            .attr("fill", "blue")
            .attr("stroke", "#ccc")
            .attr("stroke-width", 1)
            .call(drag(simulation));

        simulation.on("tick", function () {
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
        });
    });

</script>