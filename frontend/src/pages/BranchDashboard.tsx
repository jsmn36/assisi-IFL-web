import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Building, UploadCloud, FileText, Image as ImageIcon, Video, Megaphone, Calendar, FileType2, LogOut, CheckCircle2, Edit, Trash2, Eye, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/Toast';
import { getUploads, saveUpload, deleteUpload } from '@/lib/storage';

export default function BranchDashboard() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  
  const [uploadType, setUploadType] = useState<'media' | 'document' | 'notice'>('media');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'details' | 'manage'>('upload');
  
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const thumbnailInputRef = React.useRef<HTMLInputElement>(null);
  const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);

  const [manageContents, setManageContents] = useState<any[]>([]);
  const [previewContent, setPreviewContent] = useState<any | null>(null);

  // Branch details state
  const [branchName, setBranchName] = useState(user?.first_name || user?.username || '');
  const [branchLocation, setBranchLocation] = useState('');
  const [branchTag, setBranchTag] = useState('');

  useEffect(() => {
    if (activeTab === 'manage') {
      getUploads().then((localContents) => {
        setManageContents(localContents.filter((r: any) => r.institution_name === branchName || true));
      });
    }
  }, [activeTab, branchName]);

  const handleLogout = async () => {
    try {
      await logout();
      showToast('Logged out successfully');
    } catch (err) {
      console.error(err);
    }
  };

  const handleMockUpload = (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    setTimeout(async () => {
      // Store all uploads to our demo global state so they show up across the site
      let determinedType: string = uploadType;
      if (uploadType === 'media' && selectedFile?.type.startsWith('video/')) {
        determinedType = 'video';
      } else if (uploadType === 'media' && selectedFile?.type.startsWith('image/')) {
        determinedType = 'image';
      }

      const newContent = {
        id: Date.now(),
        title: uploadTitle || (selectedFile ? selectedFile.name : 'Untitled'),
        content: uploadDescription || 'New content update',
        mediaBlob: selectedFile || null,
        media_url: selectedFile ? URL.createObjectURL(selectedFile) : null,
        institution_name: branchName || 'Assisi Institute',
        institution_id: 1,
        hashtags: branchTag ? `#${branchTag.replace(/\s+/g, '')} #Update` : '#AssisiUpdates',
        created_at: new Date().toISOString(),
        type: determinedType,
      };

      await saveUpload(newContent);

      setIsUploading(false);
      setSelectedFile(null);
      setThumbnailFile(null);
      setUploadTitle('');
      setUploadDescription('');
      showToast('Content uploaded successfully!', 'success');
    }, 1500);
  };

  const handleUpdateDetails = (e: React.FormEvent) => {
    e.preventDefault();
    showToast('Branch details updated successfully!', 'success');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-indigo-500/10 rounded-xl flex items-center justify-center border border-indigo-500/20">
            <Building className="h-5 w-5 text-indigo-500" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Institution Dashboard</h1>
            <p className="text-xs text-slate-400">Content Management System</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="hidden sm:inline text-sm font-semibold text-slate-300">
            {user?.first_name || user?.username}
          </span>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-bold transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row gap-8 py-8 items-start">
        
        {/* Left Sidebar */}
        <aside className="w-full md:w-64 flex-shrink-0 space-y-2">
          <div className="mb-6 px-3">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Branch Menu</h2>
          </div>
          
          <button 
            onClick={() => setActiveTab('upload')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'upload' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
          >
            <UploadCloud className="h-5 w-5" />
            1. Post a new
          </button>
          
          <button 
            onClick={() => setActiveTab('details')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'details' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
          >
            <Edit className="h-5 w-5" />
            2. Edit branch details
          </button>
          
          <button 
            onClick={() => setActiveTab('manage')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'manage' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
          >
            <FileText className="h-5 w-5" />
            3. Manage contents
          </button>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 w-full space-y-8">
          
          {/* Welcome Section */}
          <div className="pb-4 border-b border-white/5">
            <h2 className="text-3xl font-extrabold text-white">Welcome, {user?.first_name || user?.username}</h2>
            <p className="text-slate-400 mt-1">Manage your institutional presence.</p>
          </div>

          {activeTab === 'upload' && (
            <div className="bg-slate-900 border border-white/5 rounded-3xl overflow-hidden shadow-xl shadow-black/20 animate-in fade-in duration-300">
              <div className="p-6 sm:p-10">
                <form onSubmit={handleMockUpload} className="space-y-8">
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <UploadCloud className="text-indigo-400 h-5 w-5" /> 
                      Unified Upload Center
                    </h3>
                    <p className="text-sm text-slate-400">Upload media, documents, or publish official notices and events all in one place.</p>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div className="space-y-5">
                        <div>
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Content Type</label>
                          <select 
                            value={uploadType}
                            onChange={(e) => setUploadType(e.target.value as any)}
                            className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none appearance-none"
                          >
                            <option value="media">Media (Images & Video)</option>
                            <option value="document">Document (PDF, DOC, TXT)</option>
                            <option value="notice">News, Notice or Event</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Title</label>
                          <input 
                            type="text" 
                            required 
                            value={uploadTitle}
                            onChange={(e) => setUploadTitle(e.target.value)}
                            placeholder="e.g. Annual Sports Meet 2026" 
                            className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none" 
                          />
                        </div>
                        <div>
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Description / Details</label>
                          <textarea 
                            required 
                            rows={4} 
                            value={uploadDescription}
                            onChange={(e) => setUploadDescription(e.target.value)}
                            placeholder="Write the details here..." 
                            className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none resize-none" 
                          />
                        </div>
                      </div>

                      <div className="flex flex-col">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Attach File</label>
                        <div 
                          className="flex-1 border-2 border-dashed border-slate-700 rounded-2xl p-8 flex flex-col items-center justify-center text-center hover:border-indigo-500 hover:bg-indigo-500/5 transition-colors cursor-pointer group"
                          onClick={() => fileInputRef.current?.click()}
                        >
                          <div className="h-16 w-16 bg-slate-800 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <UploadCloud className="h-8 w-8 text-indigo-400" />
                          </div>
                          <p className="text-sm font-bold text-white mb-2">
                            {selectedFile ? selectedFile.name : 'Drag and drop file here'}
                          </p>
                          <p className="text-xs text-slate-500 leading-relaxed">
                            {selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : <>Supports MP4, JPG, PNG, PDF, DOC, TXT<br/>Maximum file size: 50MB</>}
                          </p>
                          <button type="button" className="mt-6 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white rounded-lg transition-colors">
                            {selectedFile ? 'Change File' : 'Browse Files'}
                          </button>
                          <input 
                            type="file" 
                            className="hidden" 
                            accept="image/*,video/mp4,.pdf,.doc,.docx,.txt" 
                            ref={fileInputRef}
                            onChange={(e) => {
                              if (e.target.files && e.target.files[0]) {
                                setSelectedFile(e.target.files[0]);
                                if (!e.target.files[0].type.startsWith('video/')) {
                                  setThumbnailFile(null);
                                }
                              }
                            }}
                          />
                        </div>

                        {/* Optional Thumbnail for Video */}
                        {selectedFile && selectedFile.type.startsWith('video/') && (
                          <div className="mt-4">
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Video Thumbnail (Optional)</label>
                            <div 
                              className="border-2 border-dashed border-slate-700 rounded-xl p-4 flex flex-col items-center justify-center text-center hover:border-indigo-500 hover:bg-indigo-500/5 transition-colors cursor-pointer"
                              onClick={() => thumbnailInputRef.current?.click()}
                            >
                              <div className="h-10 w-10 bg-slate-800 rounded-full flex items-center justify-center mb-2">
                                <ImageIcon className="h-5 w-5 text-indigo-400" />
                              </div>
                              <p className="text-sm font-bold text-white">
                                {thumbnailFile ? thumbnailFile.name : 'Upload Thumbnail Image'}
                              </p>
                              <input 
                                type="file" 
                                className="hidden" 
                                accept="image/*" 
                                ref={thumbnailInputRef}
                                onChange={(e) => {
                                  if (e.target.files && e.target.files[0]) {
                                    setThumbnailFile(e.target.files[0]);
                                  }
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 flex justify-end">
                    <button 
                      type="submit"
                      disabled={isUploading}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-8 rounded-xl transition flex items-center gap-2 disabled:opacity-50"
                    >
                      {isUploading ? 'Uploading...' : <><UploadCloud className="h-5 w-5" /> Publish Content</>}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {activeTab === 'details' && (
            <div className="bg-slate-900 border border-white/5 rounded-3xl overflow-hidden shadow-xl shadow-black/20 animate-in fade-in duration-300">
              <div className="p-6 sm:p-10">
                <form onSubmit={handleUpdateDetails} className="space-y-6 max-w-xl">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                    <Building className="text-indigo-400 h-5 w-5" /> 
                    Edit Branch Details
                  </h3>
                  
                  <div>
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Branch Name</label>
                    <input type="text" value={branchName} onChange={e => setBranchName(e.target.value)} required className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none" />
                  </div>
                  
                  <div>
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Location</label>
                    <input type="text" value={branchLocation} onChange={e => setBranchLocation(e.target.value)} placeholder="e.g. Kidangoor" required className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none" />
                  </div>
                  
                  <div>
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Tagline / Subject Focus</label>
                    <input type="text" value={branchTag} onChange={e => setBranchTag(e.target.value)} placeholder="e.g. Science & Discipline" className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none" />
                  </div>

                  <div className="pt-4">
                    <button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-8 rounded-xl transition">
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {activeTab === 'manage' && (
            <div className="bg-slate-900 border border-white/5 rounded-2xl p-6 shadow-xl shadow-black/20 animate-in fade-in duration-300">
              <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <FileText className="text-indigo-400 h-5 w-5" />
                Manage Previous Contents
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-950/50 text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-semibold rounded-tl-lg">File / Title</th>
                      <th className="px-4 py-3 font-semibold">Type</th>
                      <th className="px-4 py-3 font-semibold">Date</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold text-right rounded-tr-lg">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {manageContents.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                          No content uploaded yet in this session.
                        </td>
                      </tr>
                    ) : (
                      manageContents.map((item, i) => (
                        <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-4 py-3 font-medium text-white max-w-[200px] truncate">{item.title}</td>
                          <td className="px-4 py-3 text-slate-400">
                            <span className="px-2 py-1 bg-slate-800 rounded-md text-xs uppercase tracking-wider">{item.type}</span>
                          </td>
                          <td className="px-4 py-3 text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td>
                          <td className="px-4 py-3">
                            <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-bold">
                              <CheckCircle2 className="h-3 w-3" /> Published
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex justify-end gap-2">
                              <button 
                                onClick={() => setPreviewContent(item)}
                                className="p-2 hover:bg-indigo-500/10 rounded-lg text-slate-400 hover:text-indigo-400 transition-colors" 
                                title="Preview Content"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button 
                                onClick={async () => {
                                  await deleteUpload(item.id);
                                  const updated = manageContents.filter(c => c.id !== item.id);
                                  setManageContents(updated);
                                  showToast('Content deleted', 'success');
                                }}
                                className="p-2 hover:bg-rose-500/10 rounded-lg text-slate-400 hover:text-rose-400 transition-colors" 
                                title="Delete Content"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Preview Modal */}
          <AnimatePresence>
            {previewContent && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
                onClick={() => setPreviewContent(null)}
              >
                <motion.div 
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.95, opacity: 0 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-slate-900 border border-white/10 rounded-2xl overflow-hidden max-w-2xl w-full shadow-2xl"
                >
                  <div className="flex items-center justify-between p-4 border-b border-white/10">
                    <h3 className="font-bold text-white truncate pr-4">{previewContent.title}</h3>
                    <button onClick={() => setPreviewContent(null)} className="p-2 hover:bg-white/10 rounded-full text-slate-400 transition-colors">
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                  <div className="bg-black relative aspect-video flex items-center justify-center">
                    {previewContent.type === 'video' ? (
                      <video 
                        src={previewContent.media_url} 
                        controls 
                        autoPlay 
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="p-8 text-center text-slate-400">
                        Preview not available for this format.
                      </div>
                    )}
                  </div>
                  <div className="p-4 bg-slate-900">
                    <p className="text-sm text-slate-300">{previewContent.content}</p>
                    <p className="text-xs text-indigo-400 font-medium mt-2">{previewContent.hashtags}</p>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
