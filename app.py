from flask import Flask, render_template, request
import math

app = Flask(__name__)
contador_circuitos=[]
ampacidad = {
"14":15,
"12":20,
"10":30,
"8":40,
"6":55,
"4":70,
"3":85,
"2":95,
"1":110,
"1/0":125,
"2/0":145,
"3/0":165,
"4/0":195
}

resistencia = {
"14":10.7,
"12":6.73,
"10":4.226,
"8":2.653,
"6":1.671,
"4":1.053,
"3":0.833,
"2":0.661,
"1":0.524,
"1/0":0.415,
"2/0":0.329,
"3/0":0.2610,
"4/0":0.2050
}

area_awg={
"14":6.258,
"12":8.581,
"10":13.61,
"8":23.61,
"6":32.71,
"4":53.16,
"3":62.77,
"2":74.71,
"1":100.8,
"1/0":119.7,
"2/0":143.4,
"3/0":172.8,
"4/0":208.8
}

# PVC
pvc_tabla = {
"1/2":100,
"3/4":168,
"1":279,
"1 1/4":456,
"1 1/2":600,
"2":940
}

emt_tabla = {
"1/2":78,
"3/4":138,
"1":222,
"1 1/4":383,
"1 1/2":527,
"2":860
}

calibres = list(ampacidad.keys())

ptm_tabla=[
15,20,25,30,35,
40,45,50,60,70,
80,90,100,110,125,
150,175,200,225,250,
300,350,400,450,500,
600,700,800,1000,1200,
1600,2000,2500,3000,4000,
5000,6000
]

tierra_tabla={
15:"14 AWG",
20:"12 AWG",
60:"10 AWG",
100:"8 AWG",
200:"6 AWG",
300:"4 AWG",
400:"3 AWG",
500:"2 AWG",
600:"1 AWG",
800:"1/0 AWG",
1000:"2/0 AWG",
1200:"3/0 AWG",
1600:"4/0 AWG"
}

@app.route("/", methods=["GET","POST"])
def index():

    resultado=None

    if request.method=="POST":

        sistema=request.form["sistema"]
        V=float(request.form["voltaje"])
        carga=float(request.form["carga"])
        unidad=request.form["unidad"]
        DT=float(request.form["distancia"])
        FP=float(request.form["fp"])

        # VALIDAR FP
        if FP<0.65 or FP>1:
            resultado={
            "error":"⚠️ Factor de potencia inválido. Debe estar entre 0.65 y 1.00"
            }
            return render_template("index.html", resultado=resultado)

        # VALIDAR DISTANCIA
        if DT>110:
            resultado={
            "error":"⚠️ Distancia mayor a 110 m. Recomendaciones: dividir carga, instalar subtablero o aumentar tensión."
            }
            return render_template("index.html", resultado=resultado)

        # CONVERSION DE VOLTAJE:
        # El usuario siempre ingresa voltaje línea a línea (208/214/220 V).
        # Para monofásico y bifásico, la carga opera con voltaje de fase (L-N),
        # que equivale a V_linea / sqrt(3).
        # Para trifásico se mantiene el voltaje línea a línea en la fórmula.
        if sistema=="trifasico":
            V_calculo=V
        else:
            V_calculo=V/math.sqrt(3)

        # convertir carga
        if unidad=="kVA":
            S=carga*1000

        elif unidad=="kW":
            S=(carga*1000)/FP

        elif unidad=="W":
            S=carga/FP

        elif unidad=="VA":
            S=carga

        elif unidad=="HP":
            S=(carga*745.7)/(FP*0.85)

        # calcular corriente
        if sistema=="trifasico":
            I=S/(math.sqrt(3)*V_calculo)
            polos=3

        elif sistema=="bifasico":
            I=S/V_calculo
            polos=2

        else:
            I=S/V_calculo
            polos=1

        # VALIDAR CORRIENTE
        if I>195:
            resultado={
            "error":"⚠️ Corriente superior a 195 A. Recomendaciones: dividir carga, usar mayor tensión o sistema trifásico."
            }
            return render_template("index.html", resultado=resultado)

        indice=None

        for i,awg in enumerate(calibres):

            if I<=ampacidad[awg]:
                indice=i
                break

        if indice is None:

            resultado={
            "error":"⚠️ La carga supera el conductor 4/0 AWG."
            }

            return render_template("index.html", resultado=resultado)

        calibres_probados=[]

        while True:

            calibre=calibres[indice]

            RC=resistencia[calibre]

            if sistema=="trifasico":

                CT=((math.sqrt(3)*DT*RC*I)/(1000*V_calculo))*100

            else:

                CT=((2*DT*RC*I)/(1000*V_calculo))*100

            calibres_probados.append(
            f"{calibre} AWG → CT = {round(CT,2)} %"
            )

            if CT<=3:
                break

            indice+=1

            if indice>=len(calibres):
                break

        # VALIDAR RETIE
        if CT>3:

            resultado={
            "error":"🔴 RETIE NO CUMPLE. Ni usando 4/0 AWG se logra caída menor al 3 %. Recomendaciones: aumentar tensión, reducir distancia o dividir carga."
            }

            return render_template("index.html", resultado=resultado)

        # PTM superior o igual
        PTM=ptm_tabla[-1]

        for valor in ptm_tabla:

            if valor>=I:
                PTM=valor
                break

        neutro=calibre

        tierra=""

        for proteccion in tierra_tabla:

            if PTM<=proteccion:
                tierra=tierra_tabla[proteccion]
                break

        conductores=3

        area_total=conductores*area_awg[calibre]

        diametro_pvc=""

        for tubo,area in pvc_tabla.items():

            if area_total<=area:
                diametro_pvc=tubo
                break

        diametro_emt=""

        for tubo,area in emt_tabla.items():

            if area_total<=area:
                diametro_emt=tubo
                break

        retie="🟢 Cumple RETIE"

        contador_circuitos.append(
        str(len(contador_circuitos)+1)
        )

        circuito_str="-".join(contador_circuitos)

resultado={

    "voltaje":V,
    "voltaje_fase":round(V_calculo,2),
    "corriente":round(I,2),
    "ptm":PTM,
    "polos":polos,
    "fase":calibre,
    "neutro":neutro,
    "tierra":tierra,
    "caida":round(CT,3),
    "distancia":DT,
    "fp":FP,
    "retie":retie,
    "pvc":diametro_pvc,
    "emt":diametro_emt,
    "circuito":circuito_str,
    "intentos":calibres_probados

}

return render_template("index.html", resultado=resultado)

if __name__=="__main__":
    app.run(debug=True)
