import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import colour
from colour.plotting import *
from scipy.signal import find_peaks

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
        self.botao2.pack(pady= 1)
        
        self.botao3 = tk.Button(
            self.main_frame,
            text='CFMS',
            command=self.plot_single_cmfs
        )
        self.botao3.pack(pady= 1)
        
#        self.botao4 = tk.Button(
#            self.main_frame,
#            text='Absorbance',
#            command=self.absorbance
#        )
#        self.botao4.pack(pady= 1)
        
        self.frame_graph = tk.Frame(self.main_frame, bg='white')
        self.frame_graph.pack(fill=tk.BOTH, expand=True)
        
        self.label_imagem = tk.Label(self.main_frame)
        self.label_imagem.pack()
        
    def plot_single_cmfs(self):
        plot_single_cmfs(
           "Stockman & Sharpe 2 Degree Cone Fundamentals",
            y_label="Sensitivity",
            bounding_box=(390, 870, 0, 1.1),
        )
    
    def carregar_imagem(self, value = None):
        
        filename = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.png *.jpeg"), ("Todos arquivos", "*.*")]
        )
        if not filename:
            return
        
        self.img_arr = cv2.imread(filename)
        self.img_arr = cv2.cvtColor(self.img_arr, cv2.COLOR_BGR2RGB)
        
        self.img = Image.fromarray(self.img_arr)
        self.img = self.img.resize((775, 45))
            
        imagetk = ImageTk.PhotoImage(image=self.img)                
        self.label_imagem.config(image=imagetk)
        self.label_imagem.image = imagetk    
            
    def plotar_espectro_rgb(self):
        
        self.carregar_imagem(value=0)
        
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
        ax.grid(True)
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        #self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
        #self.toolbar.update()
            
    def plotar_espectro_continuo(self):

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        try:
            altura, self.largura, _ = self.img_arr.shape
            
            cmfs = colour.MSDS_CMFS["Stockman & Sharpe 2 Degree Cone Fundamentals"]
            wavelengths = cmfs.wavelengths
            s_r = cmfs.values[:, 0]
            s_g = cmfs.values[:, 1]
            s_b = cmfs.values[:, 2]
            
            self.comprimentos_onda_mapeados = np.linspace(380, 780, self.largura)
    
            self.s_r_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_r)
            self.s_g_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_g)
            self.s_b_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_b)
            
            espectro = (self.espectro_r * self.s_r_interp + self.espectro_g * self.s_g_interp + self.espectro_b * self.s_b_interp)

            espectro /=  np.max(espectro)
            
            picos = find_peaks(espectro)
            
            self.fig = plt.Figure(figsize=(9, 4), dpi=100)
            ax = self.fig.add_subplot(111)
            ax.plot(self.comprimentos_onda_mapeados, espectro, color='darkviolet')
            ax.scatter(self.comprimentos_onda_mapeados[picos[0]], espectro[picos[0]], color='black', alpha = 1)
            
            ax.set_xlabel("Comprimento de Onda (nm)")
            ax.set_ylabel("Intensidade Relativa")
            ax.set_title("Espectro estimado (ponderado pela percepção humana)")
            ax.set_xlim(380, 780)
            ax.grid(True, alpha=0.3)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            #self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
            #self.toolbar.update()

        except Exception as e:
            tk.messagebox.showerror("Erro", f"Falha ao gerar espectro:\n{str(e)}")
        
#    def absorbance(self):
#        self.carregar_imagem(value=1)
#    
#        if self.canvas:
#            self.canvas.get_tk_widget().destroy()
#        if self.toolbar:
#            self.toolbar.destroy()
#        
#        try:
#            
#            iluminantes = colour.SDS_ILLUMINANTS['D65']
#            iluminantes_interp = np.interp(self.comprimentos_onda_mapeados, iluminantes.wavelengths, iluminantes.values)     
#            
#            R_c = np.maximum(np.sum(iluminantes_interp * self.s_r_interp), 1e-6)
#            G_c = np.maximum(np.sum(iluminantes_interp * self.s_g_interp), 1e-6)
#            B_c = np.maximum(np.sum(iluminantes_interp * self.s_b_interp), 1e-6)
#            
#            R = np.clip(self.espectro_r, 1e-6, 1.0)
#            G = np.clip(self.espectro_g, 1e-6, 1.0)
#            B = np.clip(self.espectro_b, 1e-6, 1.0)
#            
#            R_absorbance = -np.log10(R/R_c)
#            G_absorbance = -np.log10(G/G_c)            
#            B_absorbance = -np.log10(B/B_c)
#            absorbance = (R_absorbance + G_absorbance + B_absorbance) / 3
#
#            self.fig = plt.Figure(figsize=(9, 4), dpi=100)
#            ax = self.fig.add_subplot(111)
#            
#            ax.plot(self.comprimentos_onda_mapeados, absorbance, color='darkviolet')
#            ax.set_xlabel("Comprimento de Onda (nm)")
#            ax.set_ylabel("Intensidade Relativa")
#            ax.set_title("Espectro Estimado")
#            ax.set_xlim(380, 780)
#            ax.grid(True, alpha=0.3)
#            
#            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
#            self.canvas.draw()
#            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
#            
#            self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
#            self.toolbar.update()
#
#        except Exception as e:
#            tk.messagebox.showerror("Erro", f"Falha ao executar o comando:\n{str(e)}")
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = EspectroscopiaApp(root)
    root.mainloop()