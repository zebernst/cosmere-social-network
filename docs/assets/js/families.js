/* d3 force graph for family relationships *
 *     [uses force-directed-graph.js]      */

// persist graph
let graph;

const data = d3.json(dataUrl)
    .then(function (data) {
        let svg = d3.select('svg#force-graph')
            .datum(data);

        let legend = [
            {color: "#1f77b4", world: "Sel"},
            {color: "#ff7f0e", world: "Roshar"},
            {color: "#2ca02c", world: "Scadrial"},
            {color: "#d62728", world: "Nalthis"},
            {color: "#9467bd", world: "Threnody"},
            {color: "#8c564b", world: "First of the Sun"},
            {color: "#e377c2", world: "Taldain"}
            ];

        // create graph
        graph = forceDirectedGraph()
            .width(window.innerWidth)
            .height(window.innerHeight)
            .radius(5)
            .legendKey('world')
            .colorDomain(_.map(legend, 'world'))
            .colorRange(_.map(legend, 'color'));

        // bind graph to svg
        svg.call(graph);
    });