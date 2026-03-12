from flask import Flask, render_template, request
import math

app = Flask(__name__)

# tabla 310.15(B)(16) Ampacidad cobre 60°C
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

# tabla 8 cobre Resistencia ohm/km
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
#tabla 5 (THHN, THWN, THWN-2) seccion aprox mm2
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
#tabla 4, art 352- tubo (conduit) de pvc rigido tipo A (pvc)
pvc_tabla = {
"1/2":100,
"1/4":168,
"1":279,
"1 1/4":456,
"1 1/2":600,
"2":940
}

#tabla 240.6(A) valores nominales estandar en A
calibres = list(ampacidad.keys())
ptm_tabla=[15,20,25,30,35,
           40,45,50,60,70,
           80,90,100,110,125,
           150, 175,200,225,250,
           300,350,400,450,500,
           600,700,800,1000,1200,
           1600,2000,2500,3000,4000,
           5000,6000]

#tabla 250.122 cobre
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

        # convertir kVA a VA
        if unidad=="kVA":
            S=carga*1000
        elif unidad=="W":
            S=carga
        elif unidad=="VA":
            S=carga
        elif unidad=="HP":
            S=(carga*(745.7/1))/0.85

        # calcular corriente
        if sistema=="trifasico":
            I=S/(math.sqrt(3)*V)
            polos=3
        elif sistema=="bifasico":
            I=S/V
            polos=2
        else:
            I=S/V
            polos=1

        indice=None
        for i,awg in enumerate(calibres):
            if I<ampacidad[awg]:
                indice=i
                break
        if indice is None:
            resultado={
            "voltaje":V,
            "corriente":round(I,2),
            "ptm":"No calculada",
            "polos":polos,
            "fase":"Mayor a 4/0 AWG",
            "neutro":"Mayor a 4/0 AWG",
            "tierra":"No calculada",
            "caida":"No calculada",
            "distancia":DT,
            "intentos":[]
            }
            return render_template("index.html", resultado=resultado)
        NC=1

        calibres_probados=[]
        
        while True:
            calibre=calibres[indice]
            RC=resistencia[calibre]

            if sistema=="trifasico":
                CT=((math.sqrt(3)*DT*RC*I)/(1000*V*NC))*100
            else:
                CT=((2*DT*RC*I)/(1000*V*NC))*100
            calibres_probados.append(
            f"{calibre} AWG → CT ={round(CT,2)} % ")

            if CT <=3:
                break
            indice+=1
            if indice >=len(calibres):
                break


        PTM=ptm_tabla[0]
        diferencia_min = abs(I - PTM)
        for valor in ptm_tabla:
            diferencia = abs(I - valor)
            if diferencia < diferencia_min:
                diferencia_min = diferencia
                PTM=valor

        neutro=calibre

        tierra=""
        for proteccion in tierra_tabla:
            if PTM <=proteccion:
                tierra=tierra_tabla[proteccion]
                break
        conductores=3
        area_total = conductores* area_awg[calibre]
        diametro_pvc=""
        for tubo,area in  pvc_tabla.items():
            if area_total <= area:
                diametro_pvc = tubo
                break
        if CT<= 3:
            retie = "🟢Cumple RETIE"
        else:
            retie = "🔴No cumple RETIE"


        resultado={
            "voltaje":V,
            "corriente":round(I,2),
            "ptm":PTM,
            "polos":polos,
            "fase":calibre,
            "neutro":neutro,
            "tierra":tierra,
            "caida":round(CT,3),
            "distancia":DT,
            "retie":retie,
            "pvc": diametro_pvc,
            "intentos":calibres_probados
              }

    return render_template("index.html",resultado=resultado)
if __name__=="__main__":
    app.run(debug=True)