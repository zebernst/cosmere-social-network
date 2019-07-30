/* d3 force graph for family relationships *
 *     [uses force.js]     */

// persist graph
let graph;

const data = d3.json(dataUrl)
    // create graph
    .then(function (data) {
        const svg = d3.select('svg#force-graph')
            .datum(data);

        const legend = [
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

        // pass data through
        return data;
    })

    // handle autocomplete
    .then(function (data) {
        const searchbar = $( "#node-search" );

        searchbar
            .autocomplete({
                source: function (request, response) {
                   if (request.term === "") {
                       response([]);
                       return;
                   }

                   let matches = _(data.nodes)
                       .filter(node => _(node.names)
                               .some(s => _.includes(s.toLowerCase(), request.term.toLowerCase())))
                       .map(n => ({name: n.id, aliases: _.difference(n.names, [n.id]), value: n.id}))
                       .value();

                   response(matches)
                },
                select: function (event, ui) {
                    graph.api.update(graph.api.component(graph.api.data, ui.item.value));
                }
            })
            .focusout(function () {
                // if empty field is unfocused, update graph to show all nodes
                if (!$(this).val()) {
                    graph.api.update(graph.api.data);
                }
            });

        searchbar
            .data("ui-autocomplete")
                ._renderItem = function (ul, item) {
                    console.log(item);
                    return $( "<li>" )
                        .append("<a>" + item.name
                            + `<span style='font-size: 60%; padding-left: 1em'>${item.aliases.join(", ")}</span>`
                            + "</a>")
                        .appendTo(ul)
                }
    });
