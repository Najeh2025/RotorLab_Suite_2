import streamlit as st
import ross as rs

def test_minimal_multirotor_streamlit():
    st.title("Test Minimal ROSS MultiRotor")
    
    try:
        st.write(f"**Version de ROSS utilisée :** {rs.__version__}")
        
        # Matériel de base
        steel = rs.materials.steel
        
        # 1. Éléments du Rotor 1
        shaft1 = [rs.ShaftElement(L=0.25, i_d=0, o_d=0.05, material=steel, n=0)]
        gear1 = rs.GearElement(n=1, id=1, mass=2.0, Ie=0.1, Ip=0.1) 
        
        # 2. Éléments du Rotor 2
        shaft2 = [rs.ShaftElement(L=0.25, i_d=0, o_d=0.05, material=steel, n=0)]
        gear2 = rs.GearElement(n=0, id=2, mass=2.0, Ie=0.1, Ip=0.1) 
        
        # 3. Assemblage des Rotors individuels
        rotor1 = rs.Rotor(shaft_elements=shaft1, disk_elements=[gear1])
        rotor2 = rs.Rotor(shaft_elements=shaft2, disk_elements=[gear2])
        
        # 4. Création du MultiRotor
        mr = rs.MultiRotor(rotor1, rotor2)
        
        st.success("🎉 Succès ! Le MultiRotor a été assemblé correctement avec la nouvelle API.")
        st.write("Voici l'objet généré :", mr)
        
    except Exception as e:
        st.error("❌ Échec lors de l'assemblage du MultiRotor.")
        st.exception(e) # Streamlit va formater l'erreur proprement sur la page

# Exécution de la fonction pour Streamlit
test_minimal_multirotor_streamlit()
