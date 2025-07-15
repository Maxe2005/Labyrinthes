
class Chrono(tk.Frame):
    def __init__(self, boss=None, max_time=3600):
        tk.Frame.__init__(self,boss)
        self.boss = boss
        self.time = 0
        self.max_time = max_time
        self.running = False
        self.create_widgets()
    
    def create_widgets(self):
        self.label = tk.Label(self, text="00:00", fg="red", font=("Arial", 30))
        self.label.pack()
        self.boss.bind("<q>",self.start)
        self.boss.bind("<w>",self.stop)
        self.boss.bind("<e>",self.reset)
    
    def start(self,event=None):
        if not(self.running) :
            self.running = True
            self.update_time()
    
    def stop(self,event=None):
        self.running = False
    
    def reset(self,event=None):
        self.running = False
        self.time = 0
        self.update_label()
    
    def update_time(self):
        if self.running:
            self.time += 1
            self.update_label()
            self.test_fin()
            self.after(1000, self.update_time)
    
    def update_label(self):
        #hours = self.time // 3600
        minutes = (self.time // 60) % 60
        seconds = self.time % 60
        self.label.config(text=f"{minutes:02d}:{seconds:02d}")
        
    def test_fin (self) :
        if self.max_time == self.time :
            self.running = False
            messagebox.showinfo ('Fin du temps impartis','Le temps accordé est dépassé !',icon = 'error')
