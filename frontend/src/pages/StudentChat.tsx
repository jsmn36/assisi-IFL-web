import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import StudentLayout from '@/components/StudentLayout';
import api from '@/lib/api';
import { Send, Search, MessageCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/Toast';

export default function StudentChat() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [conversations, setConversations] = useState<any[]>([]);
  const [activePartner, setActivePartner] = useState<any | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessageText, setNewMessageText] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const messageEndRef = useRef<HTMLDivElement>(null);

  const queryUserId = searchParams.get('userId');
  const queryUsername = searchParams.get('username');
  const queryName = searchParams.get('name');
  const queryAvatar = searchParams.get('avatar');

  useEffect(() => {
    if (queryUserId && queryUsername) {
      setTimeout(() => {
        setActivePartner({
          id: parseInt(queryUserId, 10),
          username: queryUsername,
          name: queryName || queryUsername,
          profile_pic_url: queryAvatar || null
        });
        setSearchParams({});
      }, 0);
    }
  }, [queryUserId, queryUsername, queryName, queryAvatar, setSearchParams]);

  const loadConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadChatHistory = async (partnerId: number) => {
    try {
      const history = await api.getChatHistory(partnerId);
      setMessages(history);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    setTimeout(() => {
      loadConversations();
    }, 0);
  }, []);

  // Poll chat history every 3 seconds for real-time update feel
  useEffect(() => {
    if (!activePartner) return;
    setTimeout(() => {
      loadChatHistory(activePartner.id);
    }, 0);

    const interval = setInterval(() => {
      loadChatHistory(activePartner.id);
    }, 3000);

    return () => clearInterval(interval);
  }, [activePartner]);

  // Autoscroll to bottom when new messages arrive
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSearchUsers = async (val: string) => {
    setSearchTerm(val);
    if (!val.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const searchRes = await api.searchSocial(val);
      const filtered = (searchRes.users || []).filter((u: any) => u.id !== user?.id);
      setSearchResults(filtered);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectPartner = (partner: any) => {
    setActivePartner(partner);
    setSearchTerm('');
    setSearchResults([]);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessageText.trim() || !activePartner) return;
    try {
      const sentMsg = await api.sendMessage(activePartner.id, newMessageText);
      setMessages(prev => [...prev, sentMsg]);
      setNewMessageText('');
      loadConversations();
    } catch {
      showToast('Failed to send message.', 'error');
    }
  };

  return (
    <StudentLayout>
      <div className="h-screen flex border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        
        {/* Left Side: Conversation List & User Search */}
        <div className="w-80 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between">
          <div className="p-4 border-b border-slate-250 dark:border-slate-800 space-y-3">
            <h2 className="font-extrabold text-base flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-indigo-500" />
              Chats
            </h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search students to message..."
                value={searchTerm}
                onChange={(e) => handleSearchUsers(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 pl-9 pr-4 py-2 rounded-xl text-xs focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white"
              />
            </div>
          </div>

          {/* User Search Results or Active Conversations List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {searchTerm ? (
              <div className="space-y-1">
                <p className="text-[10px] text-slate-400 font-bold uppercase px-2 mb-2">Search Results</p>
                {searchResults.length === 0 ? (
                  <p className="text-xs text-slate-400 italic px-2">No students found.</p>
                ) : (
                  searchResults.map((user) => (
                    <div
                      key={user.id}
                      onClick={() => handleSelectPartner(user)}
                      className="flex items-center gap-3 p-2.5 rounded-xl cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition"
                    >
                      <img
                        src={user.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${user.username}`}
                        alt={user.username}
                        className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-850"
                      />
                      <div>
                        <h4 className="font-bold text-xs">{user.name}</h4>
                        <p className="text-[10px] text-slate-400">@{user.username}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-1">
                {conversations.length === 0 ? (
                  <div className="text-center text-slate-400 py-10">
                    <p className="text-xs font-semibold">No chats started yet.</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">Use search bar above to start chat.</p>
                  </div>
                ) : (
                  conversations.map((conv) => {
                    const isActive = activePartner?.id === conv.partner_id;
                    return (
                      <div
                        key={conv.partner_id}
                        onClick={() => handleSelectPartner({
                          id: conv.partner_id,
                          name: conv.partner_name,
                          username: conv.partner_username,
                          profile_pic_url: conv.partner_profile_pic
                        })}
                        className={`flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition ${
                          isActive 
                            ? 'bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/50' 
                            : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                        }`}
                      >
                        <img
                          src={conv.partner_profile_pic || `https://api.dicebear.com/7.x/adventurer/svg?seed=${conv.partner_username}`}
                          alt={conv.partner_username}
                          className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800"
                        />
                        <div className="overflow-hidden flex-1">
                          <div className="flex justify-between items-center">
                            <h4 className="font-bold text-xs truncate">{conv.partner_name}</h4>
                            <span className="text-[9px] text-slate-400">{new Date(conv.last_message_time).toLocaleDateString([], {month: 'short', day: 'numeric'})}</span>
                          </div>
                          <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate mt-0.5">
                            {conv.last_message}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Message Room */}
        <div className="flex-1 flex flex-col justify-between bg-slate-50 dark:bg-slate-950">
          {activePartner ? (
            <>
              {/* Header */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center gap-3">
                <img
                  src={activePartner.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${activePartner.username}`}
                  alt={activePartner.username}
                  className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800 border"
                />
                <div>
                  <h3 className="font-bold text-xs text-slate-900 dark:text-white leading-none">
                    {activePartner.name}
                  </h3>
                  <span className="text-[9px] text-indigo-500 dark:text-indigo-400 font-semibold uppercase tracking-wider block mt-1">
                    @{activePartner.username}
                  </span>
                </div>
              </div>

              {/* Message List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => {
                  const isOwnMessage = msg.sender_id === user?.id;
                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[70%] p-3.5 rounded-2xl shadow-sm text-xs leading-relaxed ${
                        isOwnMessage
                          ? 'bg-indigo-600 text-white rounded-tr-none'
                          : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-855 dark:text-slate-200 rounded-tl-none'
                      }`}>
                        <p>{msg.content}</p>
                        <span className={`text-[8px] font-bold block mt-1.5 text-right ${
                          isOwnMessage ? 'text-indigo-250' : 'text-slate-400'
                        }`}>
                          {new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                    </div>
                  );
                })}
                <div ref={messageEndRef} />
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex gap-2.5">
                <input
                  type="text"
                  placeholder={`Message @${activePartner.username}...`}
                  value={newMessageText}
                  onChange={(e) => setNewMessageText(e.target.value)}
                  className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-4 py-2.5 rounded-xl text-xs focus:outline-none focus:border-indigo-500 text-slate-850 dark:text-white"
                  required
                />
                <button
                  type="submit"
                  disabled={!newMessageText.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 rounded-xl flex items-center justify-center transition disabled:opacity-50"
                >
                  <Send className="h-4.5 w-4.5" />
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 dark:text-slate-500">
              <MessageCircle className="h-12 w-12 opacity-30 text-indigo-400 mb-3" />
              <p className="font-bold text-sm">No Active Chat</p>
              <p className="text-xs mt-1">Select a student from the sidebar or search to start messaging.</p>
            </div>
          )}
        </div>

      </div>
    </StudentLayout>
  );
}
