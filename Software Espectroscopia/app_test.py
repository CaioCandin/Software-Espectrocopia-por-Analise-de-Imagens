import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import colour
from colour.plotting import *

class EspectroscopiaApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry('1200x700')
        self.root.title('Software de Espectroscopia')
        self.root.configure(bg='#f0f0f0')
        
        self.img_arr = None
        self.fig = None
        self.canvas = None
        self.toolbar = None
        
        self.criar_interface()
        
    def criar_interface(self):
        self.main_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.botao1 = tk.Button(
            self.main_frame,
            text='Espectro RGB',
            command=self.plotar_espectro_rgb,
        )
        self.botao1.pack(pady= 10)
       
        self.botao2 = tk.Button(
            self.main_frame,
            text='Espectro continuo',
            command=self.plotar_espectro_continuo,
        )
        self.botao2.pack(pady= 10)
        
        self.botao3 = tk.Button(
            self.main_frame,
            text='CFMS',
            command=plot_single_cmfs
        )
        self.botao3.pack(pady= 10)
        
        self.frame_graph = tk.Frame(self.main_frame, bg='white')
        self.frame_graph.pack(fill=tk.BOTH, expand=True)
        
        self.label_imagem = tk.Label(self.main_frame)
        self.label_imagem.pack()
        
    def carregar_imagem(self):
        
        filename = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.png *.jpeg"), ("Todos arquivos", "*.*")]
        )
        if not filename:
            return
        
        self.img_arr = cv2.imread(filename)
        self.img_arr = cv2.cvtColor(self.img_arr, cv2.COLOR_BGR2RGB)
        
        self.img = Image.fromarray(self.img_arr)
        self.img = self.img.resize((875, 45))
            
        imagetk = ImageTk.PhotoImage(image=self.img)                
        self.label_imagem.config(image=imagetk)
        self.label_imagem.image = imagetk
        
    def plotar_espectro_rgb(self):
        
        self.carregar_imagem()
        
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
                    
        self.altura, self.largura, _ = self.img_arr.shape
        self.espectro_r = [np.mean(self.img_arr[:, x, 0])/255 for x in range(self.largura)]
        self.espectro_g = [np.mean(self.img_arr[:, x, 1])/255 for x in range(self.largura)]
        self.espectro_b = [np.mean(self.img_arr[:, x, 2])/255 for x in range(self.largura)]
                
        self.fig = plt.Figure(figsize=(9, 4))
        ax = self.fig.add_subplot(111)
                
        ax.plot(self.espectro_r, color='red')#, label="Vermelho (R)")
        ax.plot(self.espectro_g, color='green')#, label="Verde (G)")
        ax.plot(self.espectro_b, color='blue')#, label="Azul (B)")
            
        ax.set_title("Espectroscopia RGB da Imagem", fontsize=12)
        ax.set_xlabel("Posição Horizontal na Imagem")
        ax.set_ylabel("Intensidade Normalizada")
        ax.legend()
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        #self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
        #self.toolbar.update()
            
    def plotar_espectro_continuo(self):
        self.carregar_imagem()
        
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        try:
            # Obter dimensões da imagem
            altura, largura, _ = self.img_arr.shape
        
            # 1. Coletar valores RGB para cada posição horizontal
            R = np.array([np.mean(self.img_arr[:, x, 0])/255 for x in range(largura)])
            G = np.array([np.mean(self.img_arr[:, x, 1])/255 for x in range(largura)])
            B = np.array([np.mean(self.img_arr[:, x, 2])/255 for x in range(largura)])
            
            # 2. Obter dados CMFS
            cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
            wavelengths = cmfs.wavelengths
            s_r = cmfs.values[:, 0]
            s_g = cmfs.values[:, 1]
            s_b = cmfs.values[:, 2]
            
            # 3. Mapear posições horizontais para comprimentos de onda
            comprimentos_onda_mapeados = np.linspace(380, 780, largura)
            
            # 4. Interpolar os valores CMFS para corresponder à resolução da imagem
            s_r_interp = np.interp(comprimentos_onda_mapeados, wavelengths, s_r)
            s_g_interp = np.interp(comprimentos_onda_mapeados, wavelengths, s_g)
            s_b_interp = np.interp(comprimentos_onda_mapeados, wavelengths, s_b)
            
            # 5. Calcular o espectro para cada posição
            espectro = (R * s_r_interp + G * s_g_interp + B * s_b_interp)
            
            # 6. Criar o gráfico
            self.fig = plt.Figure(figsize=(9, 4), dpi=100)
            ax = self.fig.add_subplot(111)
            ax.plot(comprimentos_onda_mapeados, espectro, color='darkviolet')
            
            ax.set_xlabel("Comprimento de Onda (nm)")
            ax.set_ylabel("Intensidade Relativa")
            ax.set_title("Espectro Reconstruído Dinâmico")
            ax.set_xlim(380, 780)
            ax.grid(True, alpha=0.3)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            tk.messagebox.showerror("Erro", f"Falha ao gerar espectro:\n{str(e)}")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = EspectroscopiaApp(root)
    root.mainloop()