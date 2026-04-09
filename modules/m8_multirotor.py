import ross as rs

def test_minimal_multirotor():
    print(f"Version de ROSS utilisée : {rs.__version__}")
    
    # Matériel de base
    steel = rs.materials.steel
    
    # 1. Éléments du Rotor 1 (L'arbre va du nœud 0 au nœud 1)
    shaft1 = [rs.ShaftElement(L=0.25, i_d=0, o_d=0.05, material=steel, n=0)]
    gear1 = rs.GearElement(n=1, id=1, mass=2.0, Ie=0.1, Ip=0.1) # Attaché au nœud 1
    
    # 2. Éléments du Rotor 2 (L'arbre va du nœud 0 au nœud 1)
    shaft2 = [rs.ShaftElement(L=0.25, i_d=0, o_d=0.05, material=steel, n=0)]
    gear2 = rs.GearElement(n=0, id=2, mass=2.0, Ie=0.1, Ip=0.1) # Attaché au nœud 0
    
    # 3. Assemblage des Rotors individuels (Les engrenages vont dans disk_elements)
    rotor1 = rs.Rotor(shaft_elements=shaft1, disk_elements=[gear1])
    rotor2 = rs.Rotor(shaft_elements=shaft2, disk_elements=[gear2])
    
    # 4. Création du MultiRotor
    try:
        mr = rs.MultiRotor(rotor1, rotor2)
        print("🎉 Succès ! Le MultiRotor a été assemblé correctement.")
    except Exception as e:
        print(f"❌ Échec lors de l'assemblage du MultiRotor. L'erreur est : \n{e}")

if __name__ == "__main__":
    test_minimal_multirotor()
