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
            raise RuntimeError("El micròfon no està disponible al núvol.")
            
        audio_data = sd.rec(int(self.duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32')
        sd.wait()
        return audio_data.flatten()

    def obtener_frecuencia_dominante(self, audio_data):
        """
        Aïlla automàticament el pic de màxim impacte del cop, aplica una finestra 
        matemàtica i extreu la freqüència dominant (Hz) de manera estable.
        """
        if len(audio_data) == 0:
            return 0.0
            
        # 1. Trobar el moment exacte del cop (pic de màxima amplitud)
        idx_max = np.argmax(np.abs(audio_data))
        
        # 2. Retallar una finestra precisa al voltant del cop (20 mil·lisegons abans, 200 ms després)
        # Això elimina silencis, eco i soroll de fons recollit pel navegador del mòbil
        margen_antes = int(self.sample_rate * 0.02)
        margen_despues = int(self.sample_rate * 0.20)
        
        inicio = max(0, idx_max - margen_antes)
        fin = min(len(audio_data), idx_max + margen_despues)
        audio_recortado = audio_data[inicio:fin]
        
        if len(audio_recortado) < 100:
            audio_recortado = audio_data

        # 3. Aplicar finestra de Hanning per evitar distorsions espectrals
        ventana = np.hanning(len(audio_recortado))
        audio_ventaneado = audio_recortado * ventana

        # 4. Transformada Ràpida de Fourier (FFT)
        fft_result = np.fft.fft(audio_ventaneado)
        frecuencias = np.fft.fftfreq(len(fft_result), 1 / self.sample_rate)
        
        mitad = len(frecuencias) // 2
        frecuencias = frecuencias[:mitad]
        amplitudes = np.abs(fft_result)[:mitad]
        
        # Filtratge d'amplituds vàlides per a tap tuning de guitarres (50 Hz - 1000 Hz)
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
        
        v_sonido = np.sqrt(E / rho)
        
        if freq_medida <= 0:
            return grosor_actual, round(v_sonido, 2), f_obj
            
        grosor_nou = grosor_actual * (f_obj / freq_medida)
        return round(grosor_nou, 2), round(v_sonido, 2), f_obj
