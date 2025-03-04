import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# Charger la liste des identifiants
identifiants = pd.read_csv("test_data.csv")["SK_ID_CURR"].tolist()

# Charger la distribution des valeurs (avant la sélection de la variable)
df_distribution = pd.read_csv("train_sample.csv")

# Titre principal
st.title("Scoring Crédit Bancaire")


# Interface Streamlit - Sidebar pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choisissez une page", ["Scoring Client", "Importance des Variables", "Analyse d'une Variable"])

# Sélection de l'ID client (présent sur toutes les pages)
client_id = st.sidebar.selectbox("Sélectionner un ID client...", ["Sélectionner..."] + identifiants, index=0)


# Seuil de décision affiché uniquement en information
SEUIL_DECISION = 0.46

# Récupération immédiate des informations client
if client_id != "Sélectionner...":
    url = f"https://appliscoring-1f1f7c4e1003.herokuapp.com/client/{client_id}"
    response = requests.get(url)

    if response.status_code == 200:
        st.session_state["data"] = response.json()

# Affichage des informations client dès qu'elles sont disponibles
if "data" in st.session_state:
    data = st.session_state["data"]
    
    st.sidebar.header("Informations Client")
    st.sidebar.write(f"**Âge :** {data['age']:.1f} ans" if data['age'] is not None else "**Âge :** Non renseigné")
    st.sidebar.write(f"**Revenu :** {data['income']:.0f} €" if data['income'] is not None else "**Revenu :** Non renseigné")
    st.sidebar.write(f"**Montant du crédit :** {data['credit_amount']:.0f} €" if data['credit_amount'] is not None else "**Montant du crédit :** Non renseigné")
    st.sidebar.write(f"**Ancienneté emploi :** {data['employment_length']:.1f} ans" if data['employment_length'] is not None else "**Ancienneté emploi :** Non renseigné")

# Page 1 : Scoring Client
if page == "Scoring Client":
    if client_id != "Sélectionner..." and "data" in st.session_state:
        data = st.session_state["data"]

        if st.button("Calculer le Score"):
            score_client = data["score"]
            decision_api = data["decision"]

            # Palette adaptée au daltonisme (bleu/orange)
            couleur = "#1f77b4" if decision_api == "Accepte" else "#ff7f0e"

            # Affichage des résultats
            st.write(f"**Seuil de décision :** {SEUIL_DECISION}")
            st.markdown(
                f"<p style='color: {couleur}; font-size:22px; font-weight:bold;'>"
                f"Score du client : {score_client:.2f}</p>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p style='color: {couleur}; font-size:24px; font-weight:bold;'>"
                f"Décision : Crédit {decision_api}</p>",
                unsafe_allow_html=True
            )

            # Graphique accessible avec hachures et légende claire
            fig, ax = plt.subplots(figsize=(6, 2))
            ax.barh(y=0, width=score_client, color=couleur, height=0.05, hatch="////")  # Hachures pour accessibilité
            ax.axvline(SEUIL_DECISION, color="black", linestyle="--", label="Seuil 0.46")
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.46, 1])
            ax.set_yticks([])
            ax.legend()

            st.pyplot(fig) 

            # Description textuelle pour l’accessibilité
            st.write(f"Le score du client est représenté par une barre horizontale en couleur (bleue pour les crédits accéptés et orange pour les crédits refusés). "
                     f"Un seuil de décision ({SEUIL_DECISION}) est marqué par une ligne noire. "
                     f"Si le score dépasse ce seuil, le crédit est accepté.")

            st.session_state["importance_des_variables"] = True
    else:
        st.warning("Veuillez sélectionner un ID client pour voir les informations et calculer le score.")


# Page 2 : Importance des Variables
elif page == "Importance des Variables":
    if "data" in st.session_state and st.session_state.get("importance_des_variables", False):
        data = st.session_state["data"]

        # Importance Globale
        st.subheader("Importance globale")
        fig, ax = plt.subplots(figsize=(18, 10))

        # Définition des couleurs et des hachures
        colors = ["#1f77b4" if val > 0 else "#ff7f0e" for val in data["global_importance_values"]]
        hatches = ["xxxx" if val > 0 else "////" for val in data["global_importance_values"]]

        bars = ax.barh(data["global_importance_names"], data["global_importance_values"], color=colors)

        # Définitiondes ticks 
        ax.set_yticks(range(len(data["global_importance_names"])))
        ax.set_yticklabels(data["global_importance_names"], fontsize=15, fontweight="bold")

        # Ajout des valeurs sur les barres, positionnées à l'extérieur
        for bar, hatch, value in zip(bars, hatches, data["global_importance_values"]):
            bar.set_hatch(hatch)
            offset = 0.0001  # Décalage ajusté pour rapprocher les valeurs des barres
            if value > 0:
                ax.text(bar.get_width() + offset, bar.get_y() + bar.get_height()/2, f"{value:.2f}", 
                        va='center', ha='left', fontsize=15, fontweight="bold", color="black")
            else:
                ax.text(bar.get_width() - offset, bar.get_y() + bar.get_height()/2, f"{value:.2f}", 
                        va='center', ha='right', fontsize=15, fontweight="bold", color="black")

        # Ajout d'une ligne verticale pour marquer zéro
        ax.axvline(0, color="black", linestyle="--", linewidth=2)
        ax.set_xlabel("Impact sur le modèle", fontsize=16)

        st.pyplot(fig)

        # Explication des résultats
        st.write("L'importance globale représente l'effet moyen de chaque variable sur le modèle.")

        st.write("")  # Espacement entre les graphiques
        st.write("") 
        st.write("") 

        # Importance Locale
        st.subheader("Importance Locale")
        fig, ax = plt.subplots(figsize=(18, 10))

        colors = ["#1f77b4" if val > 0 else "#ff7f0e" for val in data["local_importance_values"]]
        hatches = ["xxxx" if val > 0 else "////" for val in data["local_importance_values"]]

        bars = ax.barh(data["local_importance_names"], data["local_importance_values"], color=colors)

        # Définition des ticks 
        ax.set_yticks(range(len(data["local_importance_names"])))
        ax.set_yticklabels(data["local_importance_names"], fontsize=15, fontweight="bold")

        for bar, hatch, value in zip(bars, hatches, data["local_importance_values"]):
            bar.set_hatch(hatch)
            offset = 0.0001  # Ajustement de la position des valeurs
            if value > 0:
                ax.text(bar.get_width() + offset, bar.get_y() + bar.get_height()/2, f"{value:.2f}", 
                        va='center', ha='left', fontsize=15, fontweight="bold", color="black")
            else:
                ax.text(bar.get_width() - offset, bar.get_y() + bar.get_height()/2, f"{value:.2f}", 
                        va='center', ha='right', fontsize=15, fontweight="bold", color="black")

        ax.axvline(0, color="black", linestyle="--", linewidth=2)
        ax.set_xlabel("Impact pour ce client", fontsize=16)

        st.pyplot(fig)

        # Explication des résultats
        st.write("")
        st.write("L'importance locale montre l'effet spécifique de chaque variable pour ce client.")

    else:
        st.warning("Veuillez d'abord calculer le score du client dans la page 'Scoring Client'.")

# Page 3 : Analyse d'une Variable
elif page == "Analyse d'une Variable":
    if "data" in st.session_state:
        data = st.session_state["data"]
        
        # Sélection d'une variable parmi les variables importantes
        variable = st.selectbox("Choisissez une variable importante", list(data["client_important_values"].keys()))
        
        if variable:
            client_value = data["client_important_values"][variable]
            
            # Sélectionner uniquement la variable et TARGET
            df_selected = df_distribution[["TARGET", variable]]
            
            # Déterminer le type de variable et adapter le titre
            title = f"Moyenne de TARGET selon la catégorie {variable}" if df_selected[variable].nunique() == 2 else f"Distribution de {variable}"
            st.subheader(title)
            fig, ax = plt.subplots(figsize=(16, 10))

            # Définition des couleurs adaptées au daltonisme
            color_non_def = "#1f78b4"  # Bleu foncé
            color_def = "#ff7f0e"  # Orange

            # Vérification si la variable est binaire (0 ou 1)
            if df_selected[variable].nunique() <= 2:  
                unique_values = df_selected[variable].unique()  # Récupération des valeurs uniques présentes

                # Définition de la palette en fonction des valeurs uniques
                if len(unique_values) == 2:
                    adapted_palette = [color_non_def, color_def]  # Deux couleurs si les deux catégories (0 et 1) sont présentes
                else:
                    adapted_palette = [color_non_def] if unique_values[0] == 0 else [color_def]  # Une seule couleur selon la catégorie unique
                
                # Création du graphique avec Seaborn
                barplot = sns.barplot(x=df_selected[variable], y=df_selected["TARGET"], 
                                      hue=df_selected[variable].astype(str), 
                                      errorbar=None,  # Désactivation de l'affichage des intervalles de confiance
                                      palette=adapted_palette, legend=False, ax=ax)
                
                # Affichage des valeurs moyennes au-dessus des barres
                for p in barplot.patches:
                    ax.text(p.get_x() + p.get_width() / 2, p.get_height() + 0.01, f"{p.get_height():.2f}", 
                            ha='center', fontsize=14, fontweight="bold", color="black")
                
                # Création de la légende
                ax.legend(labels=["Non-défaillant (0)", "Défaillant (1)"], 
                          title=variable, loc='best', fontsize=14)

            else:
                sns.kdeplot(df_selected[df_selected["TARGET"] == 0][variable], label="Non-défaillant (0)", 
                            color=color_non_def, fill=True, alpha=0.4, linestyle='dashed', linewidth=3)
                sns.kdeplot(df_selected[df_selected["TARGET"] == 1][variable], label="Défaillant (1)", 
                            color=color_def, fill=True, alpha=0.4, linestyle='solid', linewidth=3)

                # Ajouter la légende pour le graphique continu
                ax.legend(labels=["Non-défaillant (0)", "Défaillant (1)"], title=variable, loc='best', fontsize=14)

            # Ligne verticale pour la valeur du client
            ax.axvline(client_value, color="black", linestyle="--", linewidth=3, label="Valeur client")
            
            ax.set_xlabel(variable, fontsize=16)
            ax.set_ylabel("Densité" if df_selected[variable].nunique() > 2 else "Moyenne TARGET", fontsize=16)

            st.pyplot(fig)

    else:
        st.warning("Veuillez d'abord calculer le score du client dans la page 'Scoring Client'.")

