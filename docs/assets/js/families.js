/* d3 force graph for family relationships *
 *    [setup located in d3-force.js]       */

let graph = forceDirectedGraph();
let dataset;

data.then(function (data) {
    dataset = data;

    let svg = d3.select('svg#force-graph')
        .datum(data);

    // populate color space
    graph = graph
        .width(window.innerWidth)
        .height(window.innerHeight)
        .radius(5)
        .colorDomain([...new Set(data.nodes.map(n => n.world))]);

    svg.call(graph);
});