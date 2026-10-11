import numpy as np

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None  # Evita que la nube colapse si no hay PortAudio o sounddevice

class AnalizadorTapTuning:
    def __init__(self, sample_rate=44100, duration=1.5):
        """
        Inicialitza els paràmetres de mostratge i la base de dades física 
        de les fustes tonals del projecte (fons, aros i tapes).
        """
        self.sample_rate = sample_rate
        self.duration = duration
        
        # Base de dades de fustes amb freqüències objectiu i propietats mecàniques
        self.maderas_db = {
            "Palisandre": {
                "E": 11.5e9,          # Mòdul de Young longitudinal (Pa)
                "rho": 830.0,         # Densitat (kg/m^3)
                "f_objetivo": 220.0,  # Freqüència objectiu per a fons (Hz)
                "rol": "Fons / Aros (Guitarra Clàssica)"
            },
            "Cipres": {
                "E": 9.5e9,           # Mòdul de Young longitudinal (Pa)
                "rho": 530.0,         # Densitat (kg/m^3)
                "f_objetivo": 235.0,  # Freqüència objectiu per a fons flamencs (Hz)
                "rol": "Fons / Aros (Guitarra Flamenca Blanca)"
            },
            "Pino Romerón": {
                "E": 9.2e9,           # Mòdul de Young longitudinal (Pa)
                "rho": 440.0,         # Densitat (kg/m^3)
                "f_objetivo": 185.0,  # Freqüència objectiu per a tapa (Hz)
                "rol": "Tapa Harmònica / Estructura"
            },
            "Cedre del Pacífic": {
                "E": 10.0e9,          # Mòdul de Young longitudinal (Pa)
                "rho": 380.0,         # Densitat (kg/m^3)
                "f_objetivo": 175.0,  # Freqüència objectiu per a tapa càlida (Hz)
                "rol": "Tapa Harmònica (Resposta càlida)"
            }
        }

    def grabar_golpe(self):
        """Activa el micròfon del dispositiu, grava el 'tap' i retorna l'array d'àudio."""
        if sd is None:
            raise RuntimeError("El micròfon no està disponible al núvol. Introdueix la freqüència manualment.")
            
        print("🎙️ Escoltant... ¡Colpeja la fusta ara!")
        audio_data = sd.rec(int(self.duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32')
        sd.wait()
        return audio_data.flatten()

    def obtener_frecuencia_dominante(self, audio_data):
        """
        Aplica la Transformada Ràpida de Fourier (FFT) per extreure 
        la freqüència dominant (Hz) del cop d'àudio dins del rang útil.
        """
        fft_result = np.fft.fft(audio_data)
        frecuencias = np.fft.fftfreq(len(fft_result), 1 / self.sample_rate)
        
        mitad = len(frecuencias) // 2
        frecuencias = frecuencias[:mitad]
        amplitudes = np.abs(fft_result)[:mitad]
        
        # Filtratge d'amplituds vàlides per a tap tuning (50 Hz - 1000 Hz)
        rango_valido = (frecuencias > 50) & (frecuencias < 1000)
        frecuencias_filtradas = frecuencias[rango_valido]
        amplitudes_filtradas = amplitudes[rango_valido]
        
        if len(amplitudes_filtradas) == 0:
            return 0.0
            
        indice_pico = np.argmax(amplitudes_filtradas)
        return round(frecuencias_filtradas[indice_pico], 2)

    def calcular_ajuste_grosor(self, madera_nom, grosor_actual, freq_medida):
        """
        Calcula la velocitat del so en el material i el gruix òptim 
        basant-se estrictament en les propietats mecàniques de la placa lliure.
        """
        if madera_nom not in self.maderas_db:
            raise ValueError("Dades de fusta no reconegudes.")
            
        info = self.maderas_db[madera_nom]
        E = info["E"]
        rho = info["rho"]
        f_obj = info["f_objetivo"]
        
        # Velocitat de propagació de l'ona longitudinal v = sqrt(E / rho)
        v_sonido = np.sqrt(E / rho)
        
        if freq_medida <= 0:
            return grosor_actual, round(v_sonido, 2), f_obj
            
        # Càlcul del nou gruix recomanat per a la placa lliure
        grosor_nou = grosor_actual * (f_obj / freq_medida)
        return round(grosor_nou, 2), round(v_sonido, 2), f_obj
