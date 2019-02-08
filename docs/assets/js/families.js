/* d3 force graph for family relationships *
 *    [setup located in d3-force.js]       */

// copy of current displayed subset (for debugging)
let displayedSubset,
    allData;

// apply data
data.then(function (data) {

    // populate color space
    color.domain([...new Set(data.nodes.map(n => n.world))]);

    // initial drawing with all data
    // (transforms links into node references)
    update(data);

    // save data globally for debugging
    allData = data;
    displayedSubset = allData;

    // update nodes with neighbor array (needs to be called after initial update())
    populateNeighbors(data);

    // add legend
    legend = legend
        .data(color.domain())
        .enter()
        .append("g")
        .attr("class", "series")
        .attr("transform", (d, i) => `translate(0, ${20 * i})`)
        .on("click", datum => { // apply filter on click
            toggleFilter("world", datum);
            displayedSubset = subset(data, filters);
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
        .attr("class", "legend-title")
        .attr("x", width/2 - (0.025 * width) + radius)
        .attr("y", -height/2 + 50 + 1)
        .attr("transform", "translate(0, -20)")
        .text("World");
});