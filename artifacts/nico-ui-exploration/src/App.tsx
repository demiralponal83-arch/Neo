import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { Menu } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden relative">
      {/* Mobile header / toggle */}
      <div className="md:hidden absolute top-0 left-0 right-0 h-16 glass-panel rounded-none border-t-0 border-l-0 border-r-0 z-20 flex items-center px-4 justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-400 to-indigo-300 flex items-center justify-center text-white font-bold text-sm shadow-md">
            M
          </div>
          <span className="font-semibold text-slate-800 tracking-tight">Nico</span>
        </div>
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-full glass-button text-slate-600"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              className="md:hidden fixed inset-0 bg-slate-900/10 backdrop-blur-sm z-30"
            />
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="md:hidden fixed inset-y-0 left-0 w-3/4 max-w-sm z-40"
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop Sidebar */}
      <div className="hidden md:block w-80 h-full p-4 pl-4 pr-2">
        <Sidebar />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 h-full pt-16 md:pt-4 pb-4 pr-4 pl-4 md:pl-2">
        <ChatArea />
      </div>
    </div>
  );
}
