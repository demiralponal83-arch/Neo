import React from 'react';
import { Plus, MessageSquare, Settings, X, Search } from 'lucide-react';
import { motion } from 'framer-motion';

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const history = [
    { id: 1, title: 'Uff, çok yoruldum falan', date: 'Bugün', active: true },
    { id: 2, title: 'Haftasonu planı', date: 'Dün', active: false },
    { id: 3, title: 'React Hooks açıklaması', date: 'Önceki 7 gün', active: false },
    { id: 4, title: 'Kahve demlerken oranlar', date: 'Önceki 7 gün', active: false },
    { id: 5, title: 'Of ya, bu kod çalışmıyor', date: 'Önceki 30 gün', active: false },
  ];

  return (
    <div className="glass-panel h-full w-full rounded-3xl flex flex-col overflow-hidden relative">
      
      {/* Header: User Avatar */}
      <div className="p-5 flex items-center justify-between border-b border-white/30 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-400 to-indigo-300 flex items-center justify-center text-white font-bold text-lg shadow-md relative overflow-hidden">
            <span className="relative z-10">M</span>
            <div className="absolute inset-0 bg-white/20 blur-sm rounded-full mix-blend-overlay"></div>
          </div>
          <div>
            <h2 className="font-semibold text-slate-800 leading-tight">Murat</h2>
            <p className="text-xs text-slate-500 font-medium">Pro Plan</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="md:hidden p-2 text-slate-400 hover:text-slate-600 glass-button rounded-full">
            <X size={18} />
          </button>
        )}
      </div>

      {/* New Chat Button & Search */}
      <div className="p-4 flex flex-col gap-3 shrink-0">
        <button className="w-full flex items-center justify-center gap-2 py-3 px-4 glass-button rounded-2xl text-slate-700 font-medium group">
          <Plus size={18} className="group-hover:rotate-90 transition-transform duration-300" />
          <span>Yeni Sohbet</span>
        </button>
        
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Sohbetlerde ara..." 
            className="w-full py-2 pl-9 pr-4 text-sm glass-input rounded-xl text-slate-700 placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-2 scroll-smooth">
        <div className="px-3 pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Geçmiş</div>
        <div className="space-y-1 px-1">
          {history.map((item, index) => (
            <motion.button 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              key={item.id}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all duration-200 ${
                item.active 
                  ? 'bg-white/60 shadow-sm border border-white/50 text-blue-600' 
                  : 'hover:bg-white/40 text-slate-600 hover:text-slate-800'
              }`}
            >
              <MessageSquare size={16} className={item.active ? 'text-blue-500' : 'text-slate-400'} />
              <div className="flex-1 truncate">
                <p className="text-sm font-medium truncate">{item.title}</p>
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Footer Settings */}
      <div className="p-4 border-t border-white/30 shrink-0">
        <button className="flex items-center gap-3 px-3 py-2 w-full rounded-xl hover:bg-white/40 text-slate-600 hover:text-slate-800 transition-colors">
          <Settings size={18} />
          <span className="text-sm font-medium">Ayarlar</span>
        </button>
      </div>
    </div>
  );
}
