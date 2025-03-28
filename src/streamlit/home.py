import streamlit as st
import time
import os
import sys
import random 
import concurrent.futures


# Obtenir le chemin absolu du répertoire parent
dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Ajouter le chemin à sys.path, sinon PredictModel n'est pas trouvé en run
if dir_path not in sys.path:
    sys.path.append(dir_path)
from tests import check_server, test_token, test_validate_token, test_prediction, read_data

# vérifie les chemins
# print(
#     "Répertoire courant:", os.getcwd()
# )  # Vérifie si Streamlit tourne bien depuis le bon dossier
# print("sys.path:", sys.path)  # Vérifie les chemins de recherche des modules
# Stock le chemin des fichiers du streamlit
path = os.path.dirname(__file__)
print("----path", path)

# En tête
st.image(os.path.join(path, "t800.jpg"), use_container_width=True) #width=200)
st.markdown(
    "<p style='text-align: center; font-size:40px;font-weight: bold;'>Data BoT-800</p>",
    unsafe_allow_html=True,
)

if "pause" not in st.session_state:
    st.session_state.pause = False
    print("-----st.session_state.select_property_type", st.session_state.pause)
st.session_state.pause = st.checkbox("Pause", value=st.session_state.pause)

# output
if "memo" not in st.session_state:
    st.session_state.memo = []
    print("-----st.session_state.memo", st.session_state.memo)

print(st.session_state.memo[-10:])

# Afficher le mémo avec les dernières entrées
st.subheader("Flux :")
st.text("\n".join(st.session_state.memo))

print("read_data")
read_data(path)

print(st.session_state.pause)

print("loop")
while st.session_state.pause == False:
    time.sleep(random.uniform(0.1, 2))
    if st.session_state.pause == True:
        print(" ######## Pause ########")
        st.rerun()
        break
    # check_server()

    # random avec for

    # Bouton pour ajouter à l'historique
    def add_text(text):
        st.session_state.memo += text
        # Garder seulement les 100 dernières lignes
        st.session_state.memo = st.session_state.memo[-30:]
        # print(st.session_state.memo)
        st.rerun()

    text=[]
    try:
        text += test_token()
        for i in range(1, random.randint(2, 3)):
            text += test_token()
            # print("a")
        for i in range(1, random.randint(2, 3)):
            text += test_validate_token()
            # print("b")
        # for i in range(1, random.randint(2, 15)):
        #     text += test_prediction()
        # print("c")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(test_prediction) for i in range(random.randint(5, 65))
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        for result in results:
            text += result
        # print(" /// result", results)

        print("request ok")
        print(text)
    except:
        pass

    print("add_text")
    add_text(text)
