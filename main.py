"""
主機CPU/RAM/HDD使用率過高警示
"""
import wx
from wx import adv
import psutil
from wx import xrc
import time

"""
通知區域小圖示
"""
class MonitorIcon(wx.adv.TaskBarIcon):
    TRAY_TOOLTIP = 'ResourceNoticer'
    TRAY_ICON = 'icon.png'
    CPU_THRESHOLD = 50
    RAM_THRESHOLD = 75
    CPU_TOTAL_USAGE = 0
    RAM_TOTAL_USAGE = 0
    CPU_TOP_USAGES = [0, 0, 0]
    CPU_TOP_PROCESSES = ['', '', '']
    RAM_TOP_USAGES = [0, 0, 0]
    RAM_TOP_PROCESSES = ['', '', '']
    CPU_QTY = psutil.cpu_count()
    MONITOR_INTERVAL = 5000 #5秒鐘
    DURATION_COUNT = 2 #2次
    CPU_OVER_COUNT = 0
    MEM_OVER_COUNT = 0

    def __init__(self):
        super(MonitorIcon, self).__init__()
        self.set_icon(self.TRAY_ICON)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.monitor_usage)
        self.timer.Start(self.MONITOR_INTERVAL)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        new_menu_item(menu, 'Threshold Setting', self.on_setting)
        menu.AppendSeparator()
        new_menu_item(menu, 'Exit', self.on_exit)

        return menu

    def set_icon(self, path):
        icon = wx.Icon(wx.Bitmap(path))
        self.SetIcon(icon, self.TRAY_TOOLTIP)

    def on_setting(self, event):
        if hasattr(self, 'warningWindow'):
            self.warningWindow.frame.Hide()
        
        self.thresholdSetting = ThresholdSetting(self)

    def on_exit(self, event):
        self.Destroy()

    """
    監控使用率
    """
    def monitor_usage(self, event):        
        self.CPU_TOTAL_USAGE = psutil.cpu_percent()        
        self.RAM_TOTAL_USAGE = psutil.virtual_memory().percent        

        if self.CPU_TOTAL_USAGE > self.CPU_THRESHOLD:
            self.CPU_OVER_COUNT += 1        
        if self.RAM_TOTAL_USAGE > self.RAM_THRESHOLD:
            self.MEM_OVER_COUNT += 1

        if (self.CPU_OVER_COUNT >= self.DURATION_COUNT or self.MEM_OVER_COUNT >= self.DURATION_COUNT):
            instances = []
            all_processes = psutil.process_iter()
            pre_process(all_processes)
            time.sleep(1)
            all_processes = psutil.process_iter()
            for proc in all_processes:
                if proc.pid == 0:                    
                        continue

                instances.append(get_process_info(proc))

            for inst in instances:
                for i in range(0, 3):
                    if inst[3] > self.CPU_TOP_USAGES[i]:
                        self.CPU_TOP_USAGES[i] = round(inst[3], 1)
                        self.CPU_TOP_PROCESSES[i] = inst[0]

                        break

                for i in range(0, 3):
                    if inst[2] > self.RAM_TOP_USAGES[i]:
                        self.RAM_TOP_USAGES[i] = round(inst[2], 1)
                        self.RAM_TOP_PROCESSES[i] = inst[0]

                        break

            self.warningWindow = WarningWindow(self)

"""
取得處理序資源使用率
"""
def get_process_info(proc):
    try:
        if proc._pid == 0:
            return
                
        name = proc.name()
        pid = proc.pid 
        cpu = float(proc.cpu_percent(interval=0) / psutil.cpu_count()) 
        mem = float(proc.memory_percent(memtype="rss"))
    except psutil.NoSuchProcess:
        pass

    return [name, pid, mem, cpu]

"""
預處理(讓get_process_info結果正確)
"""
def pre_process(processes):
    for proc in processes:
        if proc.pid == 0:
            continue

        proc.cpu_percent(interval=0)

"""
建立選單
"""
def new_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)

    return item


"""
設定門檻視窗
"""
class ThresholdSetting(wx.App):
    def __init__(self, monitor):
        self.monitor = monitor
        self.monitor.timer.Stop()
        wx.App.__init__(self, monitor)

    def OnInit(self):
        res = xrc.XmlResource("setting.xrc")
        self.frame = res.LoadFrame(None, 'frame_Setting')
        self.wxID_OK = xrc.XRCCTRL(self.frame, "wxID_OK")
        self.wxID_CANCEL = xrc.XRCCTRL(self.frame, "wxID_CANCEL")
        self.text_Cpu = xrc.XRCCTRL(self.frame, "text_Cpu")
        self.text_Ram = xrc.XRCCTRL(self.frame, "text_Ram")
        self.text_Cpu.Value = str(self.monitor.CPU_THRESHOLD)
        self.text_Ram.Value = str(self.monitor.RAM_THRESHOLD)
        self.Bind(wx.EVT_BUTTON, self.ok, self.wxID_OK)
        self.Bind(wx.EVT_BUTTON, self.cancel, self.wxID_CANCEL)        
        self.frame.Center()
        self.frame.Show()

        return True

    def ok(self, event):
        self.monitor.CPU_OVER_COUNT = 0        
        self.monitor.MEM_OVER_COUNT = 0
        self.monitor.CPU_THRESHOLD = int(self.text_Cpu.Value)
        self.monitor.RAM_THRESHOLD = int(self.text_Ram.Value)
        self.monitor.timer.Start(self.monitor.MONITOR_INTERVAL)        
        self.frame.Hide()

    def cancel(self, event):
        self.monitor.timer.Start(self.monitor.MONITOR_INTERVAL)        
        self.frame.Hide()


class WarningWindow(wx.App):
    def __init__(self, monitor):
        self.monitor = monitor
        self.monitor.timer.Stop()
        wx.App.__init__(self, monitor)

    def OnInit(self):                
        res = xrc.XmlResource("popup.xrc")
        self.frame = res.LoadFrame(None, 'frame_Popup')
        self.text_Cpu_Total_Usage = xrc.XRCCTRL(self.frame, "text_Cpu_Total_Usage")
        self.text_Cpu_Total_Usage.SetLabel(str(self.monitor.CPU_TOTAL_USAGE))
        self.text_Cpu_Top1_Process = xrc.XRCCTRL(self.frame, "text_Cpu_Top1_Process")
        self.text_Cpu_Top1_Process.SetLabel(str(self.monitor.CPU_TOP_PROCESSES[0]))
        self.text_Cpu_Top1_Usage = xrc.XRCCTRL(self.frame, "text_Cpu_Top1_Usage")
        self.text_Cpu_Top1_Usage.SetLabel(str(self.monitor.CPU_TOP_USAGES[0]))        
        self.text_Cpu_Top2_Process = xrc.XRCCTRL(self.frame, "text_Cpu_Top2_Process")
        self.text_Cpu_Top2_Process.SetLabel(str(self.monitor.CPU_TOP_PROCESSES[1]))
        self.text_Cpu_Top2_Usage = xrc.XRCCTRL(self.frame, "text_Cpu_Top2_Usage")
        self.text_Cpu_Top2_Usage.SetLabel(str(self.monitor.CPU_TOP_USAGES[1]))        
        self.text_Cpu_Top3_Process = xrc.XRCCTRL(self.frame, "text_Cpu_Top3_Process")
        self.text_Cpu_Top3_Process.SetLabel(str(self.monitor.CPU_TOP_PROCESSES[2]))
        self.text_Cpu_Top3_Usage = xrc.XRCCTRL(self.frame, "text_Cpu_Top3_Usage")
        self.text_Cpu_Top3_Usage.SetLabel(str(self.monitor.CPU_TOP_USAGES[2]))
        self.text_Ram_Total_Usage = xrc.XRCCTRL(self.frame, "text_Ram_Total_Usage")
        self.text_Ram_Total_Usage.SetLabel(str(self.monitor.RAM_TOTAL_USAGE))
        self.text_Ram_Top1_Process = xrc.XRCCTRL(self.frame, "text_Ram_Top1_Process")
        self.text_Ram_Top1_Process.SetLabel(str(self.monitor.RAM_TOP_PROCESSES[0]))
        self.text_Ram_Top1_Usage = xrc.XRCCTRL(self.frame, "text_Ram_Top1_Usage")
        self.text_Ram_Top1_Usage.SetLabel(str(self.monitor.RAM_TOP_USAGES[0]))        
        self.text_Ram_Top2_Process = xrc.XRCCTRL(self.frame, "text_Ram_Top2_Process")
        self.text_Ram_Top2_Process.SetLabel(str(self.monitor.RAM_TOP_PROCESSES[1]))
        self.text_Ram_Top2_Usage = xrc.XRCCTRL(self.frame, "text_Ram_Top2_Usage")
        self.text_Ram_Top2_Usage.SetLabel(str(self.monitor.RAM_TOP_USAGES[1]))        
        self.text_Ram_Top3_Process = xrc.XRCCTRL(self.frame, "text_Ram_Top3_Process")
        self.text_Ram_Top3_Process.SetLabel(str(self.monitor.RAM_TOP_PROCESSES[2]))
        self.text_Ram_Top3_Usage = xrc.XRCCTRL(self.frame, "text_Ram_Top3_Usage")
        self.text_Ram_Top3_Usage.SetLabel(str(self.monitor.RAM_TOP_USAGES[2]))
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.frame.Center()
        self.frame.Show()
        
        return True

    def on_click(self, event):        
        self.monitor.CPU_OVER_COUNT = 0        
        self.monitor.MEM_OVER_COUNT = 0
        self.monitor.timer.Start(self.monitor.MONITOR_INTERVAL)        
        self.frame.Hide() 

def main():
    app = wx.App()
    MonitorIcon()
    app.MainLoop()     

if __name__ == '__main__':
    main()
