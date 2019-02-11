/* d3 force graph for family relationships *
 *    [setup located in d3-force.js]       */

let graph = forceDirectedGraph();

data.then(function (data) {

    let svg = d3.select('svg#force-graph').datum(data);

    // populate color space
    graph = graph
        .colorDomain([...new Set(data.nodes.map(n => n.world))]);

    svg.call(graph);
});