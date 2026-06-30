am5.ready(function() {

    // Create root element
    let root = am5.Root.new("match_rematch_chart");

    // Set themes
    root.setThemes([
        am5themes_Animated.new(root)
    ]);

    // Create chart
    let chart = root.container.children.push(am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        paddingLeft: 0,
        layout: root.verticalLayout
    }));

    // === DATA ===
    let data = [
        { month: "Jan", matches: 40, rematches: 10 },
        { month: "Feb", matches: 55, rematches: 15 },
        { month: "Mar", matches: 80, rematches: 25 },
        { month: "Apr", matches: 45, rematches: 12 },
        { month: "May", matches: 60, rematches: 20 }
    ];

    // === Y-AXIS (LEFT: MONTHS) ===
    let yRenderer = am5xy.AxisRendererY.new(root, {
        minGridDistance: 30,
        inversed: true // Puts Jan at the top, May at the bottom
    });

    // Hide the vertical line for a cleaner corporate look
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

    // === SERIES 1: MATCHES (HORIZONTAL BARS) ===
    let matchesSeries = chart.series.push(am5xy.ColumnSeries.new(root, {
        name: "Matches",
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: "matches",
        categoryYField: "month",
        sequencedInterpolation: true,
        tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueX}"
        })
    }));

    matchesSeries.columns.template.setAll({
        height: am5.percent(70), // Makes bars slightly thinner
        cornerRadiusTR: 5,
        cornerRadiusBR: 5,
        strokeOpacity: 0,
        fill: am5.color(0x0d9488) // Corporate Teal
    });

    // === SERIES 2: REMATCHES (OVERLAY LINE) ===
    let rematchesSeries = chart.series.push(am5xy.LineSeries.new(root, {
        name: "Rematches",
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: "rematches",
        categoryYField: "month",
        sequencedInterpolation: true,
        stroke: am5.color(0x0f172a), // Slate Blue / Dark
        strokeWidth: 3,
        tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueX}"
        })
    }));

    // Add dots (bullets) to the line
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

    // Set data for both series
    matchesSeries.data.setAll(data);
    rematchesSeries.data.setAll(data);

    // === LEGEND ===
    let legend = chart.children.push(am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
        marginBottom: 15
    }));
    legend.data.setAll(chart.series.values);

    legend.labels.template.setAll({
        fontSize: 12,
        fontWeight: "500",
        fill: am5.color(0x64748b) // Muted slate color
    });


    // Animate on load
    chart.appear(1000, 100);
    matchesSeries.appear();
    rematchesSeries.appear();
});