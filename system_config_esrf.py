import dash
from dash import dcc, html, Input, Output
import numpy as np
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
    function(energy, beam_y, wedge_x, wedge_y, bomb_x, bomb_y, cam_dist) {

        // ==========================================
        // 1. YOUR MATH GOES HERE (In JavaScript)
        // ==========================================
        // Example: Math.sin() instead of np.sin()
        // Example: Math.PI instead of np.pi

        let theta_B_rad = Math.asin( 12.398 / (energy * 3.135) ); 
        let theta_B_deg = theta_B_rad * (180 / Math.PI);

        // Calculate your beam paths, wedge coordinates, and detector positions...

        // ==========================================
        // 2. BUILD THE PLOTLY TRACES
        // ==========================================
        // JavaScript arrays use [] and objects use {}

        let main_beam = {
            x: [-15, wedge_x],
            y: [beam_y, beam_y],
            mode: 'lines',
            line: {color: 'gray', width: 4},
            name: 'Main Beam'
        };

        // Create your other traces (split beams, etc.)

        // ==========================================
        // 3. RETURN THE FIGURE DICTIONARY
        // ==========================================
        return {
            data: [main_beam], // Add all your other traces to this array
            layout: {
                title: 'Si(111) | Energy = ' + energy.toFixed(2) + ' keV | θ<sub>B</sub> ≈ ' + theta_B_deg.toFixed(2) + '°',
                xaxis: {title: 'Propagation Distance (mm)', range: [-15, 170]},
                yaxis: {title: 'Transverse Distance (mm)', range: [-35, 35], scaleanchor: 'x', scaleratio: 1},
                margin: {l: 40, r: 40, t: 60, b: 120},
                plot_bgcolor: 'white',
                uirevision: 'constant', // Crucial: Keeps the axes from jumping
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