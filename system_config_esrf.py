import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server
app.title = "IFM Configuration Visualizer"

# --- Layout (The User Interface) ---
app.layout = html.Div(style={'fontFamily': 'system-ui, -apple-system, sans-serif', 'padding': '20px'}, children=[

    # The Header
    html.H1("IFM Configuration Visualizer", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # The Main Side-by-Side Container
    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'flex-start'}, children=[

        # LEFT SIDE: The Plot (75% width)
        html.Div(style={'width': '75%', 'paddingRight': '20px'}, children=[
            dcc.Graph(id='sim-plot', style={'height': '80vh'})
        ]),

        # RIGHT SIDE: The Control Panel (25% width)
        html.Div(style={
            'width': '25%',
            'padding': '20px',
            'backgroundColor': '#f8f9fa',  # Subtle gray background for the panel
            'borderRadius': '8px',
            'border': '1px solid #e9ecef',
            'height': '80vh',
            'overflowY': 'auto'  # Adds a scrollbar if the screen is too small
        }, children=[
            html.H3("Parameters", style={'marginTop': '0', 'borderBottom': '1px solid #ccc', 'paddingBottom': '10px'}),

            # Group 1: Beam Parameters
            html.Div(style={'marginBottom': '30px'}, children=[
                html.Label("Energy (keV)", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Slider(id='energy', min=7.0, max=30.0, step=0.5, value=30.0, updatemode='drag', marks=None,
                           tooltip={"placement": "bottom", "always_visible": True}),

                html.Div(style={'height': '15px'}),  # Space inside group

                html.Label("Beam Offset Y", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Slider(id='beam_y', min=-15.0, max=15.0, step=0.5, value=0.0, updatemode='drag', marks=None,
                           tooltip={"placement": "bottom", "always_visible": True}),
            ]),

            # Group 2: The Wedge (Visually grouped with a white card)
            html.Div(
                style={'marginBottom': '30px', 'padding': '15px', 'backgroundColor': '#ffffff', 'borderRadius': '5px',
                       'border': '1px solid #ddd'}, children=[
                    html.Div("Wedge Position", style={'fontWeight': 'bold', 'color': '#666', 'marginBottom': '15px',
                                                      'textTransform': 'uppercase', 'fontSize': '0.85em'}),

                    html.Label("Wedge X", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                    dcc.Slider(id='wedge_x', min=0.0, max=22.0, step=0.5, value=15.0, updatemode='drag', marks=None,
                               tooltip={"placement": "bottom", "always_visible": True}),

                    html.Div(style={'height': '15px'}),

                    html.Label("Wedge Y", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                    dcc.Slider(id='wedge_y', min=-30.0, max=30.0, step=0.5, value=20.0, updatemode='drag', marks=None,
                               tooltip={"placement": "bottom", "always_visible": True}),
                ]),

            # Group 3: The Bomb (Visually grouped with a white card)
            html.Div(
                style={'marginBottom': '30px', 'padding': '15px', 'backgroundColor': '#ffffff', 'borderRadius': '5px',
                       'border': '1px solid #ddd'}, children=[
                    html.Div("Bomb Position", style={'fontWeight': 'bold', 'color': '#666', 'marginBottom': '15px',
                                                     'textTransform': 'uppercase', 'fontSize': '0.85em'}),

                    html.Label("Bomb X", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                    dcc.Slider(id='bomb_x', min=0.0, max=60.0, step=0.5, value=28.0, updatemode='drag', marks=None,
                               tooltip={"placement": "bottom", "always_visible": True}),

                    html.Div(style={'height': '15px'}),

                    html.Label("Bomb Y", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                    dcc.Slider(id='bomb_y', min=-100.0, max=50.0, step=0.5, value=-50.0, updatemode='drag', marks=None,
                               tooltip={"placement": "bottom", "always_visible": True}),
                ]),

            # Group 4: Detectors
            html.Div(style={'marginBottom': '10px'}, children=[
                html.Label("Camera Distance", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Slider(id='cam_dist', min=10.0, max=150.0, step=1.0, value=60.0, updatemode='drag', marks=None,
                           tooltip={"placement": "bottom", "always_visible": True}),
            ]),
        ])
    ])
])

from dash.dependencies import Input, Output

app.clientside_callback(
    """
    function(energy_kev, beam_y_offset, wedge_x, wedge_y, int_detector_x, int_detector_y, out_len) {
        let data = [];
        let shapes = [];
        let annotations = [];

        // --- 1. Physics Parameters ---
        let wavelength_A = 12.398 / energy_kev;
        let a_Si = 5.431;
        let d_333 = a_Si / Math.sqrt(27);
        let sin_theta = wavelength_A / (2 * d_333);

        if (sin_theta > 1.0) {
            return {
                data: [],
                layout: { title: "Energy too low for Bragg diffraction on Si(333)" }
            };
        }

        let theta_B_rad = Math.asin(sin_theta);
        let theta_B_deg = theta_B_rad * (180 / Math.PI);
        let m = Math.tan(theta_B_rad);

        // --- 2. Geometry Parameters ---
        let L = 22.0;
        let t = 0.15; // 150 microns
        let y_blade_min = -10.0;
        let y_blade_max = 10.0;
        let x_blade1 = 0;
        let x_blade2 = L + t;
        let x_blade3 = 2 * L + 2 * t;
        let det_x = x_blade3 + t + out_len;

        // Bomb parameters
        let body_width = 60.0;
        let body_depth = 10.0;
        let bx_min = int_detector_x - body_depth / 2;
        let bx_max = int_detector_x + body_depth / 2;
        let by_min = int_detector_y - body_width / 2;
        let by_max = int_detector_y + body_width / 2;

        // Helper function to draw rectangles
        function add_rect(x0, y0, x1, y1, fillcolor, line_color, opacity) {
            shapes.push({
                type: "rect", x0: x0, y0: y0, x1: x1, y1: y1,
                fillcolor: fillcolor, line: {color: line_color, width: 1.2},
                opacity: opacity || 1.0, layer: "below"
            });
        }

        // --- 3. Draw Static Elements ---
        // Blades
        [[x_blade1, 'Blade 1'], [x_blade2, 'Blade 2'], [x_blade3, 'Blade 3']].forEach(function(item) {
            add_rect(item[0], y_blade_min, item[0] + t, y_blade_max, '#a0c4ff', 'black', 0.8);
        });

        // Camera Body
        add_rect(det_x, -100, det_x + 50, 100, 'black', 'black');

        // AdvaPIX Sensor Chip
        let chip_length = 0.055 * 512;
        add_rect(det_x - 1, -chip_length / 2, det_x, chip_length / 2, 'gray', 'white');
        annotations.push({x: det_x + 25, y: 0, text: 'AdvaPIX Camera', showarrow: false, font: {color: 'red'}});

        // Bomb
        add_rect(bx_min, by_min, bx_max, by_max, '#555555', 'black');

        // Wedge
        let wedge_length = 20.0;
        let half_base = wedge_length * Math.tan((2.8 / 2) * (Math.PI / 180));
        shapes.push({
            type: "path",
            path: `M ${wedge_x - half_base} ${wedge_y} L ${wedge_x + half_base} ${wedge_y} L ${wedge_x} ${wedge_y - wedge_length} Z`,
            fillcolor: '#add8e6', line: {color: '#00008b', width: 1.5}, opacity: 0.7, layer: "above"
        });

        // --- 4. Ray Tracing Engine ---
        function draw_beam_segment(start_x, start_y, end_x, end_y, color, label) {
            let thickness = 1.0;
            let dx = end_x - start_x;
            let dy = end_y - start_y;
            let length = Math.sqrt(dx*dx + dy*dy);
            if (length === 0) return;

            let dir_x = dx / length;
            let dir_y = dy / length;
            let perp_x = -dir_y;
            let perp_y = dir_x;

            let half_t = thickness / 2.0;
            let p1x = start_x + perp_x * half_t, p1y = start_y + perp_y * half_t;
            let p2x = start_x - perp_x * half_t, p2y = start_y - perp_y * half_t;
            let p3x = end_x - perp_x * half_t, p3y = end_y - perp_y * half_t;
            let p4x = end_x + perp_x * half_t, p4y = end_y + perp_y * half_t;

            data.push({
                x: [p1x, p2x, p3x, p4x, p1x],
                y: [p1y, p2y, p3y, p4y, p1y],
                fill: 'toself', fillcolor: color, mode: 'lines',
                line: {color: color, width: 0}, opacity: 0.85,
                name: label ? label : '',
                showlegend: !!label,
                hoverinfo: label ? 'name' : 'skip'
            });
        }

        function propagate(x_start, y_start, slope, color, target_x, label) {
            let y_target = y_start + slope * (target_x - x_start);

            // Bomb Clipping (Liang-Barsky Algorithm)
            let dx = target_x - x_start;
            let dy = y_target - y_start;
            let p = [-dx, dx, -dy, dy];
            let q = [x_start - bx_min, bx_max - x_start, y_start - by_min, by_max - y_start];
            let u1 = 0.0, u2 = 1.0;

            for (let i = 0; i < 4; i++) {
                if (p[i] === 0) {
                    if (q[i] < 0) u2 = -1;
                } else {
                    let t_val = q[i] / p[i];
                    if (p[i] < 0 && t_val > u1) {
                        u1 = t_val;
                    } else if (p[i] > 0 && t_val < u2) {
                        u2 = t_val;
                    }
                }
            }

            if (u1 <= u2 && u1 <= 1.0 && u2 >= 0.0) {
                draw_beam_segment(x_start, y_start, x_start + u1 * dx, y_start + u1 * dy, color, label);
                return null;
            } else {
                draw_beam_segment(x_start, y_start, target_x, y_target, color, label);
                return y_target;
            }
        }

        function process_blade(beams_in, blade_x, blade_idx) {
            let beams_out = [];
            for (let i = 0; i < beams_in.length; i++) {
                let bx = beams_in[i].x;
                let by = beams_in[i].y;
                let bslope = beams_in[i].slope;
                let hist = beams_in[i].hist;

                let y_target = propagate(bx, by, bslope, '#A0A0A0', blade_x + t / 2, null);

                if (y_target !== null) {
                    if (y_target >= y_blade_min && y_target <= y_blade_max) {
                        beams_out.push({x: blade_x + t / 2, y: y_target, slope: bslope, hist: hist ? hist + "*T" + blade_idx : "T" + blade_idx});
                        beams_out.push({x: blade_x + t / 2, y: y_target, slope: -bslope, hist: hist ? hist + "*R" + blade_idx : "R" + blade_idx});
                    } else {
                        beams_out.push({x: blade_x + t / 2, y: y_target, slope: bslope, hist: hist});
                    }
                }
            }
            return beams_out;
        }

        // --- 5. Execution ---
        let inc_start_y = beam_y_offset - (10 + t / 2) * m;
        let beams_leaving_1 = process_blade([{x: -10, y: inc_start_y, slope: m, hist: ""}], x_blade1, 1);
        let beams_leaving_2 = process_blade(beams_leaving_1, x_blade2, 2);
        let beams_leaving_3 = process_blade(beams_leaving_2, x_blade3, 3);

        // Group unique ports
        let unique_ports = {};
        for (let i = 0; i < beams_leaving_3.length; i++) {
            let beam = beams_leaving_3[i];
            
            // Fix the 8-ports bug: Force JavaScript to treat -0.0 and 0.0 identically
            let clean_x = Number(beam.x.toFixed(3));
            let clean_y = Number(beam.y.toFixed(3));
            let clean_slope = Number(beam.slope.toFixed(3));
            let state_key = clean_x + "_" + clean_y + "_" + clean_slope;
            
            if (!unique_ports[state_key]) {
                unique_ports[state_key] = {bx: beam.x, by: beam.y, bslope: beam.slope, hists: []};
            }
            if (beam.hist) {
                unique_ports[state_key].hists.push(beam.hist);
            }
        }

        // Compile Final Data
        let final_beams = [];
        for (let key in unique_ports) {
            let port = unique_ports[key];
            port.hists.sort();
            let combined_hist = port.hists.length > 0 ? port.hists.join(" + ") : "Direct Miss";
            let y_at_camera = port.by + port.bslope * (det_x - port.bx);
            final_beams.push({
                bx: port.bx, by: port.by, bslope: port.bslope,
                hist: combined_hist, y_cam: y_at_camera
            });
        }

        // --- Generate Stable Colors ---
        // A fixed dictionary so beam colors never change when the bomb moves or beams merge
        let fixed_palette = {
            // Top Ports
            "T1*T2*T3": "#ff7f0e", // Orange
            "T1*T2*R3": "#1f77b4", // Blue
            
            // Middle Ports (Interfering paths - The O-beam and H-beam)
            "R1*R2*T3 + T1*R2*R3": "#d62728", // Red
            "R1*R2*T3": "#d62728",            // Red (If T1R2 is blocked by the bomb)
            "T1*R2*R3": "#d62728",            // Red (If R1R2 is blocked by the bomb)

            "R1*R2*R3 + T1*R2*T3": "#2ca02c", // Green
            "R1*R2*R3": "#2ca02c",            // Green (If T1R2 is blocked)
            "T1*R2*T3": "#2ca02c",            // Green (If R1R2 is blocked)

            // Bottom Ports
            "R1*T2*R3": "#8c564b", // Brown
            "R1*T2*T3": "#9467bd", // Purple
            
            "Direct Miss": "black"
        };

        let backup_colors = ['#aec7e8', '#ffbb78', '#98df8a', '#ff9896'];
        let fallback_counter = 0;

        // --- Legend & Drawing Order ---
        // Force the legend to statically match the standard far-field vertical layout
        // (Top-to-Bottom: Orange, Red, Blue, Brown, Green, Purple)
        let visual_order = {
            "T1*T2*T3": 1,            // Top (Orange)
            "R1*R2*T3 + T1*R2*R3": 2, // Middle-Up (Red)
            "R1*R2*T3": 2,            
            "T1*R2*R3": 2,            
            "T1*T2*R3": 3,            // Top-Down (Blue)
            "R1*T2*R3": 4,            // Bottom-Up (Brown)
            "R1*R2*R3 + T1*R2*T3": 5, // Middle-Down (Green)
            "R1*R2*R3": 5,            
            "T1*R2*T3": 5,            
            "R1*T2*T3": 6,            // Bottom (Purple)
            "Direct Miss": 99
        };

        final_beams.sort((a, b) => {
            let rankA = visual_order[a.hist] || 50;
            let rankB = visual_order[b.hist] || 50;
            // If two beams have the same rank (e.g., if a fallback occurs), sort alphabetically as a backup
            if (rankA === rankB) return a.hist.localeCompare(b.hist);
            return rankA - rankB;
        });

        final_beams.forEach(beam => {
            let color = fixed_palette[beam.hist];
            if (!color) {
                color = backup_colors[fallback_counter % backup_colors.length];
                fallback_counter++;
            }
            propagate(beam.bx, beam.by, beam.bslope, color, det_x, beam.hist);
        });

        // --- 6. Return Plotly Dictionary ---
        return {
            data: data,
            layout: {
                title: 'Si(333) | Energy = ' + energy_kev.toFixed(2) + ' keV | θ<sub>B</sub> ≈ ' + theta_B_deg.toFixed(2) + '°',
                xaxis: {title: 'Propagation Distance (mm)', range: [-15, 170], showgrid: false, zeroline: false},
                yaxis: {title: 'Transverse Distance (mm)', range: [-35, 35], scaleanchor: 'x', scaleratio: 1, showgrid: false, zeroline: false},
                shapes: shapes,
                annotations: annotations,
                margin: {l: 40, r: 40, t: 60, b: 120},
                legend: {orientation: "h", yanchor: "top", y: -0.15, xanchor: "center", x: 0.5},
                plot_bgcolor: "white",
                uirevision: 'constant',
                showlegend: true
            }
        };
    }
    """,
    Output('sim-plot', 'figure'),
    [
        Input('energy', 'value'),
        Input('beam_y', 'value'),
        Input('wedge_x', 'value'),
        Input('wedge_y', 'value'),
        Input('bomb_x', 'value'),
        Input('bomb_y', 'value'),
        Input('cam_dist', 'value')
    ]
)


if __name__ == '__main__':
    app.run(debug=True)