
function show_chart(div_name, hostname, item, title, name, suffix){

    Highcharts.setOptions({
        global: { useUTC: false  },
        lang: {
            months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
            shortMonths : ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
            weekdays: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
            thousandsSep:''// 去掉千位的逗号
        }
    });

    $.getJSON('/get_data/',{"hostname": hostname, "item": item}, function (data) {
        // Create the chart
        var div_id = "#" + div_name;
        $(div_id).highcharts('StockChart', {

            chart : {
                events : {
                    load : function () {

                        // set up the updating of the chart each second
                        var series = this.series[0];
                        setInterval(function () {
                            $.ajax({
                                type: "POST",
                                url: "/get_dynamic/",
                                data: {"hostname": hostname, "item": item},
                                async: false,
                                success: function(result){
                                    var x = parseFloat(result.split(",")[0]);
                                    var y = parseFloat(result.split(",")[1]);
                                    series.addPoint([x, y], true, true);
                                }
                            });
                        }, 1000*60*5);
                    }
                }
            },

            rangeSelector : {
                buttons: [{
                    type: 'hour',
                    count: 1,
                    text: '1h'
                }, {
                    type: 'hour',
                    count: 12,
                    text: '12h'
                }, {
                    type: 'day',
                    count: 1,
                    text: '1d'
                }, {
                    type: 'month',
                    count: 1,
                    text: '1m'
                }, {
                    type: 'all',
                    text: 'All'
                }],
                inputEnabled: false, // it supports only days
                selected : 0 // all
            },

            tooltip: {
                xDateFormat: '%Y-%m-%d %H:%M:%S, %A'
            },

            xAxis: {
               type: 'datetime',
                    dateTimeLabelFormats:
                {
                    second: '%Y-%b-%e %H:%M:%S'
                }
            },

            yAxis: {
                labels: {
                    format: '{value}'+ suffix
                }
            },

            title : {
                text : title
            },

            credits: {
                href: "http://www.gomeplus.com/",
                text: "devops.meixin.com"
            },

            series : [{
                name : name,
                data : data,
                tooltip: {
                    valueDecimals: 2,
                    valueSuffix: suffix
                }
            }]
        });
    });
}

function show_network_chart(div_name, hostname) {
    var data0 = [];
    var data1 = [];
    $.ajax({
        type: "GET",
        url: "/get_data/",
        data: {"hostname": hostname, "item": "network_rx"},
        async: false,
        success: function (result) {
            data0 = result
        }
    });

    $.ajax({
        type: "GET",
        url: "/get_data/",
        data: {"hostname": hostname, "item": "network_tx"},
        async: false,
        success: function (result) {
            data1 = result;
        }
    });

    var data0 = eval("(" + data0 + ")");
    var data1 = eval("(" + data1 + ")");

    Highcharts.setOptions({
        global: {useUTC: false},
        lang: {
            months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
            shortMonths: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
            weekdays: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
            thousandsSep: ''// 去掉千位的逗号
        }
    });

    // Create the chart
    var div_id = "#" + div_name;


    $(div_id).highcharts('StockChart', {
        chart: {
            events: {
                load: function () {
                    // set up the updating of the chart each second
                    var series0 = this.series[0];
                    var series1 = this.series[1];
                    setInterval(function () {
                        $.ajax({
                            type: "POST",
                            url: "/get_dynamic/",
                            data: {"hostname": hostname, "item": "network_rx"},
                            async: false,
                            success: function (result) {
                                var x = parseInt(result.split(",")[0]);
                                var y = parseFloat(result.split(",")[1]);
                                series0.addPoint([x, y], true, true);
                            }
                        });

                        $.ajax({
                            type: "POST",
                            url: "/get_dynamic/",
                            data: {"hostname": hostname, "item": "network_tx"},
                            async: false,
                            success: function (result) {
                                var x = parseInt(result.split(",")[0]);
                                var y = parseFloat(result.split(",")[1]);
                                series1.addPoint([x, y], true, true);
                            }
                        });

                    }, 1000*60*5);
                }
            }
        },

        rangeSelector: {
            buttons: [{
                type: 'hour',
                count: 1,
                text: '1h'
            }, {
                type: 'hour',
                count: 12,
                text: '12h'
            }, {
                type: 'day',
                count: 1,
                text: '1d'
            }, {
                type: 'month',
                count: 1,
                text: '1m'
            }, {
                type: 'all',
                text: 'All'
            }],
            inputEnabled: false, // it supports only days
            selected: 0 // all
        },

        tooltip: {
            xDateFormat: '%Y-%m-%d %H:%M:%S, %A',
            pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b><br/>'
        },

        xAxis: {
            type: 'datetime',
            dateTimeLabelFormats: {
                second: '%Y-%b-%e %H:%M:%S'
            }
        },

        yAxis: {
            labels: {
                format: '{value}' + 'MB'
            }
        },

        title: {
            text: hostname + ':网卡使用情况'
        },

        credits: {
            href: "http://www.gomeplus.com/",
            text: "devops.meixin.com"
        },

        series: [{
            turboThreshold: 0,
            name: "接收流量",
            data: data0,
            tooltip: {
                valueDecimals: 4,
                valueSuffix: 'MB'
            }
        }, {
            turboThreshold: 0,
            name: "发送流量",
            data: data1,
            tooltip: {
                valueDecimals: 4,
                valueSuffix: 'MB'
            }
        }
        ]
    });

}