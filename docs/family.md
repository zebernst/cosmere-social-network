---
title: Family
permalink: /family
layout: default
---


{% include d3.html %}
<svg id="force-graph"></svg>
<script>
    var data = {{ site.data.networks.family.all | jsonify }}
</script>
<script src="{{ site.baseurl | prepend: site.url }}/assets/js/force-graph.js"></script>
