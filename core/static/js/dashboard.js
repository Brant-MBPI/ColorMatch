am5.ready(function() {

    let root = am5.Root.new("match_rematch_chart");

    // Hide logo
    if (root._logo) { root._logo.set("forceHidden", true); }

    root.setThemes([am5themes_Animated.new(root)]);

    let chart = root.container.children.push(am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "zoomY", 
        paddingLeft: 0,
        layout: root.verticalLayout
    }));

    // === DATA (Full Year) ===
    let data = [
        { month: "Jan", matches: 40, rematches: 10 },
        { month: "Feb", matches: 55, rematches: 15 },
        { month: "Mar", matches: 80, rematches: 25 },
        { month: "Apr", matches: 45, rematches: 12 },
        { month: "May", matches: 60, rematches: 20 },
        { month: "Jun", matches: 70, rematches: 22 },
        { month: "Jul", matches: 85, rematches: 30 },
        { month: "Aug", matches: 50, rematches: 15 },
        { month: "Sep", matches: 65, rematches: 18 },
        { month: "Oct", matches: 90, rematches: 35 },
        { month: "Nov", matches: 75, rematches: 25 },
        { month: "Dec", matches: 100, rematches: 40 }
    ];

    // === Y-AXIS (LEFT: MONTHS) ===
    let yRenderer = am5xy.AxisRendererY.new(root, {
        minGridDistance: 1, // THE FIX: Setting this to 1 forces EVERY label to show
        inversed: true
    });

    // Clean look
    yRenderer.grid.template.set("visible", false);

    let yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(root, {
        categoryField: "month",
        renderer: yRenderer,
        tooltip: am5.Tooltip.new(root, {})
    }));

    yAxis.data.setAll(data);

    // === X-AXIS (BOTTOM: NUMBERS) ===
    let xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
        min: 0,
        renderer: am5xy.AxisRendererX.new(root, {
            strokeOpacity: 0.1
        })
    }));

    // === CLEAN VERTICAL SCROLLBAR ===
    let scrollbarY = am5.Scrollbar.new(root, {
        orientation: "vertical",
        marginLeft: 15
    });
    chart.set("scrollbarY", scrollbarY);
    scrollbarY.startGrip.set("forceHidden", true);
    scrollbarY.endGrip.set("forceHidden", true);
    scrollbarY.get("background").setAll({ fillOpacity: 0, strokeOpacity: 0 });

    // === TOOLTIP CURSOR ===
    let cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
        behavior: "none",
        xAxis: xAxis,
        yAxis: yAxis
    }));
    cursor.lineX.set("visible", false);
    cursor.lineY.set("visible", false);

    // === SERIES 1: MATCHES ===
    let matchesSeries = chart.series.push(am5xy.ColumnSeries.new(root, {
        name: "Matches",
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: "matches",
        categoryYField: "month",
        sequencedInterpolation: true,
        tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "[bold]{categoryY}[/]\n{name}: {valueX}" 
        })
    }));

    matchesSeries.columns.template.setAll({
        height: am5.p70, 
        cornerRadiusTR: 5,
        cornerRadiusBR: 5,
        strokeOpacity: 0,
        fill: am5.color(0x0d9488)
    });

    // === SERIES 2: REMATCHES ===
    let rematchesSeries = chart.series.push(am5xy.LineSeries.new(root, {
        name: "Rematches",
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: "rematches",
        categoryYField: "month",
        sequencedInterpolation: true,
        stroke: am5.color(0x0f172a),
        strokeWidth: 3,
        tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueX}"
        })
    }));

    rematchesSeries.bullets.push(function() {
        return am5.Bullet.new(root, {
            sprite: am5.Circle.new(root, {
                radius: 5,
                fill: am5.color(0x0f172a),
                stroke: root.interfaceColors.get("background"),
                strokeWidth: 2
            })
        });
    });

    matchesSeries.data.setAll(data);
    rematchesSeries.data.setAll(data);

    // === FORCED ZOOM TO BOTTOM 5 (LARGE BARS) ===
    // We use ready event to ensure the chart is fully calculated before zooming
    chart.events.on("ready", function() {
        yAxis.zoomToIndexes(data.length - 5, data.length);
    });

    // === LEGEND ===
    let legend = chart.children.push(am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
        marginTop: 15,
        marginBottom: 10
    }));
    legend.data.setAll(chart.series.values);

    chart.appear(1000, 100);
});