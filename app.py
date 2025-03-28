#================= Import des librairies ================#
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from calendar import month_abbr, month_name
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

#================= Traitement des données ================#
df = pd.read_csv("./data.csv", index_col=0)
df = df[['CustomerID', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Transaction_Date', 'Month', 'Discount_pct']]

df['CustomerID'] = df['CustomerID'].fillna(0).astype(int)
df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'])

df['Total_price'] = df['Quantity'] * df['Avg_Price'] * (1 - (df['Discount_pct'] / 100)).round(3)

def calculer_chiffre_affaire(data):
    return data['Total_price'].sum()

def frequence_meilleure_vente(data, top=10, ascending=False):
    resultat = pd.crosstab(
        [data['Gender'], data['Product_Category']], 
        'Total vente', 
        values=data['Total_price'], 
        aggfunc= lambda x : len(x), 
        rownames=['Sexe', 'Categorie du produit'],
        colnames=['']
    ).reset_index().groupby(
        ['Sexe'], as_index=False, group_keys=True
    ).apply(
        lambda x: x.sort_values('Total vente', ascending=ascending).iloc[:top, :]
    ).reset_index(drop=True).set_index(['Sexe', 'Categorie du produit'])

    return resultat

def indicateur_du_mois(data, current_month = 12, freq=True, abbr=False): 
    previous_month = current_month - 1 if current_month > 1 else 12
    if freq : 
        resultat = data['Month'][(data['Month'] == current_month) | (data['Month'] == previous_month)].value_counts()
        # sort by index
        resultat = resultat.sort_index()
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat
    else:
        resultat = data[(data['Month'] == current_month) | (data['Month'] == previous_month)].groupby('Month').apply(calculer_chiffre_affaire)
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat

def barplot_top_10_ventes(data) :
    df_plot = frequence_meilleure_vente(data, ascending=True)
    graph = px.bar(
        df_plot,
        x='Total vente', 
        y=df_plot.index.get_level_values(1),
        color=df_plot.index.get_level_values(0), 
        barmode='group',
        title="Frequence des 10 meilleures ventes",
        labels={"x": "Fréquence", "y": "Categorie du produit", "color": "Sexe"},
        width=540, height=460
    ).update_layout(
        margin = dict(t=60)
    )
    return graph

# Evolution chiffre d'affaire
def plot_evolution_chiffre_affaire(data) :
    df_plot = data.groupby(pd.Grouper(key='Transaction_Date', freq='W')).apply(calculer_chiffre_affaire)[:-1]
    chiffre_evolution = px.line(
        x=df_plot.index, y=df_plot,
        title="Evolution du chiffre d'affaire par semaine",
        labels={"x": "Semaine", "y": "Chiffre d'affaire"},
    ).update_layout( 
        width=825, height=400,
        margin=dict(t=60, b=0),
        
    )
    return chiffre_evolution

## Chiffre d'affaire du mois
def plot_chiffre_affaire_mois(data) :
    df_plot = indicateur_du_mois(data, freq=False)
    indicateur = go.Figure(
        go.Indicator(
            mode = "number+delta",
            value = df_plot[1],
            delta = {'reference': df_plot[0]},
            domain = {'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout(
        width=200, height=200, 
        margin=dict(l=0, r=20, t=20, b=0)
    )
    return indicateur

# Ventes du mois
def plot_vente_mois(data, abbr=False) :
    df_plot = indicateur_du_mois(data, freq=True, abbr=abbr)
    indicateur = go.Figure(
        go.Indicator(
            mode = "number+delta",
            value = df_plot[1],
            delta = {'reference': df_plot[0]},
            domain = {'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout( 
        width=200, height=200, 
        margin=dict(l=0, r=20, t=20, b=0)
    )
    return indicateur

#================= Création du tableau ================#
# Colonnes pertinentes
df_table = df[['Transaction_Date', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Discount_pct']]

# Trier le tableau par date décroissante
df_table = df_table.sort_values(by='Transaction_Date', ascending=False)

# 100 dernières ventes
df_recent = df_table.head(100)

# Création du tableau
table_recent_sales = html.Div([

    # Paramétrage du titre
    html.H4(
        "Table des 100 dernières ventes", 
        style={
            "font-size": "15px",
            "font-weight": "bold",
            "margin-top": "20px",
            "margin-left": "30px",
            "width": "100%",  
        }),

    # Paramétrage du tableau
    dash_table.DataTable(
    id = "table_recent_sales",
    columns=[
        {"name": "Date", "id": "Transaction_Date"},
        {"name": "Gender", "id": "Gender"},
        {"name": "Location", "id": "Location"},
        {"name": "Product Category", "id": "Product_Category"},
        {"name": "Quantity", "id": "Quantity"},
        {"name": "Avg Price", "id": "Avg_Price"},
        {"name": "Discount Pct", "id": "Discount_pct"}
    ],
    data=df_recent.to_dict("records"),  
    page_size=10,  

    # Ajout du filtre sur toutes les colonnes du tableau
    filter_action="native",  
    sort_action="native",    

    # Paramétrage de la mise en page du tableau
    style_table={
            "width": "100%",  
            "maxWidth": "100%",
            "height": "400px",  
            "padding": "10px",
            "borderCollapse": "collapse",
        }
)
])


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Visuels utilisés
fig1 = plot_chiffre_affaire_mois(df)
fig2 = plot_vente_mois(df)
fig3 = plot_evolution_chiffre_affaire(df)
graph1 = barplot_top_10_ventes(df)
graph1.update_layout(width=550, height=500)  

#================= Création de l'application Dash ================#
app.layout = dbc.Container([
    # En-tête
    dbc.Row([
        dbc.Col(children='ECAP Store', md=9,
                style={"font-size": "20px", "font-weight": "bold"}),
        dbc.Col(html.Div([
            dcc.Dropdown(
                id='dropdown-location',  
                options=[{'label': loc, 'value': loc} for loc in df["Location"].dropna().unique()],
                multi=True,
                searchable=True,
                placeholder='Choisissez des zones...'
            )
        ]), md=3),
    ], 
    style={"width": "100%", "background-color": "#ADD8E6", "padding": "10px", "border-radius": "5px"}
    ),

    # Contenu principal
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id='fig1', figure={}), md=6,
                        style={"display": "flex", "align-items": "center", "justify-content": "center"}),
                dbc.Col(dcc.Graph(id='fig2', figure={}), md=6,
                        style={"display": "flex", "align-items": "center", "justify-content": "center"}),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='graph1', figure={}))
            ]),
        ], width=5),
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id='fig3', figure={}))]),
            dbc.Row([
                dbc.Col([
                    table_recent_sales
                ])
                ]),
        ], width=7),
    ], style={"width": "100%"}),
], fluid=True)

#================= Callback pour mettre à jour les graphiques et le tableau ================#

# Mise à jour en fonction de la sélection du dropdown
@app.callback(
    Output('fig1', 'figure'),
    Output('fig2', 'figure'),
    Output('fig3', 'figure'),
    Output('graph1', 'figure'),
    Output('table_recent_sales', 'data'),  
    Input('dropdown-location', 'value')
)
def update_charts(selected_locations):
    if not selected_locations:
        filtered_df = df  
    else:
        filtered_df = df[df["Location"].isin(selected_locations)]

# Filtrage et mise à jour les 100 dernières ventes
    filtered_table = filtered_df[['Transaction_Date', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Discount_pct']]
    filtered_table['Transaction_Date'] = pd.to_datetime(filtered_table['Transaction_Date'])
    filtered_table = filtered_table.sort_values(by='Transaction_Date', ascending=False).head(100)

    # Génération des nouveaux graphiques
    return (
        plot_chiffre_affaire_mois(filtered_df),
        plot_vente_mois(filtered_df),
        plot_evolution_chiffre_affaire(filtered_df),
        barplot_top_10_ventes(filtered_df),
        filtered_table.to_dict("records")
    )
    
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

