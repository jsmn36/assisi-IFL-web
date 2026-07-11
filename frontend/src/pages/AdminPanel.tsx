import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import Loading from '@/components/Loading';

export default function AdminPanel() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [pendingStudents, setPendingStudents] = useState<any[]>([]);
  const [allStudents, setAllStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Institution provision form
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newName, setNewName] = useState('');
  const [newAbout, setNewAbout] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newWebsite, setNewWebsite] = useState('');

  // Tab state
  const [activeTab, setActiveTab] = useState<'analytics' | 'register' | 'list' | 'students'>('analytics');

  const loadData = async () => {
    try {
      setLoading(true);
      const me = await api.getMe();
      setCurrentUser(me);

      if (me.role !== 'admin' && !me.is_superuser) {
        alert('Access denied. Super Admin permissions required.');
        navigate('/');
        return;
      }

      const [stats, insts, pending, approved] = await Promise.all([
        api.getAdminAnalytics(),
        api.getInstitutions(),
        api.getPendingStudents(),
        api.getAllStudents()
      ]);

      setAnalytics(stats);
      setInstitutions(insts);
      setPendingStudents(pending);
      setAllStudents(approved);
    } catch (err) {
      console.error('Unauthorized access to admin panel:', err);
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [navigate]);

  const handleRegisterInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newEmail.trim() || !newPassword.trim() || !newName.trim()) return;

    try {
      setLoading(true);
      const payload = {
        username: newUsername,
        email: newEmail,
        password: newPassword,
        name: newName,
        about: newAbout,
        phone: newPhone,
        website_url: newWebsite,
      };

      await api.createInstitution(payload);
      alert('Educational Institution Account & Profile provisioned successfully!');

      // Reset fields
      setNewUsername('');
      setNewEmail('');
      setNewPassword('');
      setNewName('');
      setNewAbout('');
      setNewPhone('');
      setNewWebsite('');

      // Refresh listings
      await loadData();
      setActiveTab('list');
    } catch (err) {
      alert('Error registering institution. Ensure username and email are unique.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteInstitution = async (id: number) => {
    if (!confirm('Are you sure you want to permanently delete this educational institution? This will purge their profile and ALL published feed posts.')) return;

    try {
      setLoading(true);
      await api.deleteInstitution(id);
      alert('Institution account successfully purged.');
      await loadData();
    } catch (err) {
      console.error('Error deleting institution:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveStudent = async (userId: number) => {
    try {
      setLoading(true);
      await api.approveStudent(userId);
      alert('Student registration approved!');
      await loadData();
    } catch (err) {
      alert('Failed to approve student.');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectStudent = async (userId: number) => {
    if (!confirm('Are you sure you want to reject and delete this pending registration?')) return;
    try {
      setLoading(true);
      await api.rejectStudent(userId);
      alert('Student registration rejected.');
      await loadData();
    } catch (err) {
      alert('Failed to reject student.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStudent = async (userId: number) => {
    if (!confirm('Are you sure you want to permanently delete this student account?')) return;
    try {
      setLoading(true);
      await api.deleteStudent(userId);
      alert('Student account successfully deleted.');
      await loadData();
    } catch (err) {
      alert('Failed to delete student.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    localStorage.clear();
    navigate('/login');
  };

  if (loading && !currentUser) {
    return (
      <div className="min-h-screen bg-slate-955 flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  // Calculate institution posts count from analytics
  const getInstPostsCount = (instId: number) => {
    if (!analytics || !analytics.posts_by_institution) return 0;
    const match = analytics.posts_by_institution.find((item: any) => item.id === instId);
    return match ? match.posts_count : 0;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex">
      {/* Admin Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 shrink-0 hidden md:block">
        <div className="p-6 h-full flex flex-col justify-between">
          <div className="space-y-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">🏛️</div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white to-indigo-300 bg-clip-text text-transparent">
                Assisi Admin
              </span>
            </Link>

            <div className="space-y-1">
              <button
                onClick={() => setActiveTab('analytics')}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'analytics' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                📊 Platform Metrics
              </button>
              <button
                onClick={() => setActiveTab('register')}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'register' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                ➕ Provision Institute
              </button>
              <button
                onClick={() => setActiveTab('list')}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'list' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                🏫 Manage Accounts
              </button>
              <button
                onClick={() => setActiveTab('students')}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'students' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                🎓 Student Approvals
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Role: Super Admin</p>
              <p className="text-xs font-bold text-slate-300 truncate">{currentUser?.username}</p>
            </div>
            <button
              onClick={handleLogout}
              className="w-full py-2.5 bg-rose-600/10 hover:bg-rose-600/25 border border-rose-600/20 rounded-xl text-rose-400 font-semibold text-xs transition uppercase tracking-wider"
            >
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 min-h-screen overflow-y-auto bg-slate-955/40 p-6 md:p-10 space-y-8">
        
        {/* Mobile Nav */}
        <div className="md:hidden flex items-center justify-between border-b border-slate-850 pb-4">
          <Link to="/" className="flex items-center gap-1.5">
            <span className="text-lg">🏛️</span>
            <span className="font-extrabold text-sm tracking-tight text-white">Assisi Admin</span>
          </Link>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'analytics' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Stats
            </button>
            <button
              onClick={() => setActiveTab('register')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'register' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Add
            </button>
            <button
              onClick={() => setActiveTab('list')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'list' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Manage
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'students' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Students
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-white">
            {activeTab === 'analytics' && '📊 Platform Administration Metrics'}
            {activeTab === 'register' && '➕ Provision Educational Institute'}
            {activeTab === 'list' && '🏫 Manage Educational Institution Accounts'}
            {activeTab === 'students' && '🎓 Student Registrations & Approvals'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {activeTab === 'analytics' && 'Track aggregated counts, category breakdowns, and storage profiles.'}
            {activeTab === 'register' && 'Create separate secure credentials and display profile pages for campus managers.'}
            {activeTab === 'list' && 'Deactivate, modify, or permanently remove registered campus organizations.'}
            {activeTab === 'students' && 'Review and approve pending student signups, or manage the student directory.'}
          </p>
        </div>

        {/* Tab 1: Analytics overview */}
        {activeTab === 'analytics' && analytics && (
          <div className="space-y-8 animate-fadeIn">
            {/* Top Scorecard Widgets */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              
              {/* Total Posts */}
              <div className="bg-slate-905 border border-slate-800 rounded-2xl p-6 relative overflow-hidden bg-gradient-to-tr from-slate-900 via-slate-905 to-indigo-500/5">
                <span className="text-3xl absolute top-6 right-6">📢</span>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Total Announcements</p>
                <p className="text-3xl font-extrabold mt-2 text-white">{analytics.total_posts}</p>
                <div className="mt-4 text-[10px] text-indigo-400 font-semibold flex items-center gap-1">
                  <span>📈</span> Active posts published on timeline
                </div>
              </div>

              {/* Total Institutions */}
              <div className="bg-slate-905 border border-slate-800 rounded-2xl p-6 relative overflow-hidden bg-gradient-to-tr from-slate-900 via-slate-905 to-purple-500/5">
                <span className="text-3xl absolute top-6 right-6">🏛️</span>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Registered Institutes</p>
                <p className="text-3xl font-extrabold mt-2 text-white">{analytics.total_institutions}</p>
                <div className="mt-4 text-[10px] text-purple-400 font-semibold flex items-center gap-1">
                  <span>🏛️</span> Provisioned campus workspaces
                </div>
              </div>

              {/* Active Storage */}
              <div className="bg-slate-905 border border-slate-800 rounded-2xl p-6 relative overflow-hidden bg-gradient-to-tr from-slate-900 via-slate-905 to-emerald-500/5">
                <span className="text-3xl absolute top-6 right-6">💾</span>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Asset Disk Usage</p>
                <p className="text-3xl font-extrabold mt-2 text-white">42.8 MB</p>
                <div className="mt-4 text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                  <span>⚡</span> Rich media uploading stream is optimal
                </div>
              </div>
            </div>

            {/* Category breakdown bar chart layout */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
              <h3 className="text-base font-bold text-slate-200">Category Publications Breakdown</h3>
              <div className="space-y-4">
                {Object.entries(analytics.post_types_count).map(([key, val]: [string, any]) => {
                  const percentage = analytics.total_posts > 0 ? (val / analytics.total_posts) * 100 : 0;
                  return (
                    <div key={key} className="space-y-1.5">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="capitalize text-slate-300">{key}</span>
                        <span className="text-indigo-400">{val} posts ({percentage.toFixed(0)}%)</span>
                      </div>
                      <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Provision logic */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegisterInstitution} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Account Credentials */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-850 pb-2">
                  1. Login Credentials
                </h3>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Account Username</label>
                  <input
                    type="text"
                    required
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="E.g. engineering_college"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Account Login Email</label>
                  <input
                    type="email"
                    required
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="E.g. admin@engineering.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Initial Password</label>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Display Profile Parameters */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-850 pb-2">
                  2. Display Profile Details
                </h3>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Official Display Name</label>
                  <input
                    type="text"
                    required
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="E.g. Assisi Engineering Academy"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Contact phone</label>
                  <input
                    type="text"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    placeholder="E.g. +91 98765 43210"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Website URL</label>
                  <input
                    type="url"
                    value={newWebsite}
                    onChange={(e) => setNewWebsite(e.target.value)}
                    placeholder="E.g. https://engineering.assisi.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400">Brief about / description</label>
              <textarea
                rows={3}
                value={newAbout}
                onChange={(e) => setNewAbout(e.target.value)}
                placeholder="Brief information about this school's focus, programs, and departments..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500 resize-none font-sans"
              />
            </div>

            <div className="border-t border-slate-850 pt-6 flex justify-end">
              <button
                type="submit"
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition uppercase tracking-wider"
              >
                Provision Account Credentials
              </button>
            </div>
          </form>
        )}

        {/* Tab 3: List & deletion table */}
        {activeTab === 'list' && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden animate-fadeIn">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-widest font-bold bg-slate-900/50">
                    <th className="py-4 px-6">Institution Logo & Name</th>
                    <th className="py-4 px-6">Email Contact</th>
                    <th className="py-4 px-6">Website Link</th>
                    <th className="py-4 px-6 text-center">Stories Published</th>
                    <th className="py-4 px-6 text-right">Administrative Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {institutions.map((inst) => (
                    <tr key={inst.id} className="hover:bg-slate-850/20 transition">
                      <td className="py-4 px-6 flex items-center gap-3">
                        <img
                          src={inst.logo_url || 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=40'}
                          alt={inst.name}
                          className="w-10 h-10 rounded-lg object-cover border border-slate-800"
                        />
                        <div className="truncate">
                          <p className="font-bold text-xs text-white">{inst.name}</p>
                          <p className="text-[10px] text-slate-500">ID: {inst.id}</p>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-400 font-semibold">{inst.contact_email}</td>
                      <td className="py-4 px-6 text-xs text-indigo-400">
                        {inst.website_url ? (
                          <a href={inst.website_url} target="_blank" rel="noreferrer" className="hover:underline">
                            {inst.website_url}
                          </a>
                        ) : (
                          <span className="text-slate-600">None</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-center text-xs font-bold text-slate-300">
                        {getInstPostsCount(inst.user_id)}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => handleDeleteInstitution(inst.id)}
                          className="px-3 py-1.5 rounded-lg bg-rose-600/10 hover:bg-rose-600/25 border border-rose-600/20 text-rose-400 font-semibold text-[10px] uppercase tracking-wider transition"
                        >
                          Purge Account
                        </button>
                      </td>
                    </tr>
                  ))}

                  {institutions.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-slate-500 text-xs">
                        No educational institutions registered under Assisi Social yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 4: Student Approvals & Directory */}
        {activeTab === 'students' && (
          <div className="space-y-8 animate-fadeIn">
            {/* Pending Approvals Section */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-4">
              <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-850 pb-2">
                ⏳ Pending Student Approval Requests ({pendingStudents.length})
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                      <th className="py-3 px-4">Student Details</th>
                      <th className="py-3 px-4">Admission #</th>
                      <th className="py-3 px-4">Major/Class</th>
                      <th className="py-3 px-4">Registration Email</th>
                      <th className="py-3 px-4 text-right">Approvals</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {pendingStudents.map(student => (
                      <tr key={student.id} className="hover:bg-slate-850/10 transition">
                        <td className="py-3.5 px-4 font-bold text-xs text-white">
                          {student.name} <span className="text-slate-500 font-normal">(@{student.username})</span>
                        </td>
                        <td className="py-3.5 px-4 text-xs font-semibold text-indigo-400">{student.admission_number}</td>
                        <td className="py-3.5 px-4 text-xs text-slate-355">{student.class_or_department || 'General'}</td>
                        <td className="py-3.5 px-4 text-xs text-slate-400">{student.email}</td>
                        <td className="py-3.5 px-4 text-right space-x-2">
                          <button
                            onClick={() => handleApproveStudent(student.user_id)}
                            className="bg-emerald-600/10 hover:bg-emerald-600/25 border border-emerald-600/20 text-emerald-455 font-bold text-[10px] px-3 py-1.5 rounded-lg uppercase transition"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleRejectStudent(student.user_id)}
                            className="bg-rose-605/10 hover:bg-rose-605/25 border border-rose-605/20 text-rose-455 font-bold text-[10px] px-3 py-1.5 rounded-lg uppercase transition"
                          >
                            Reject
                          </button>
                        </td>
                      </tr>
                    ))}
                    {pendingStudents.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500 text-xs italic">
                          No pending student approvals. All caught up!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Approved Students Directory */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-4">
              <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-850 pb-2">
                🎓 Active Student Directory ({allStudents.length})
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                      <th className="py-3 px-4">Name & Username</th>
                      <th className="py-3 px-4">Admission Number</th>
                      <th className="py-3 px-4">Class/Department</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {allStudents.map(student => (
                      <tr key={student.id} className="hover:bg-slate-850/10 transition">
                        <td className="py-3.5 px-4 font-bold text-xs text-white">
                          {student.name} <span className="text-slate-500 font-normal">(@{student.username})</span>
                        </td>
                        <td className="py-3.5 px-4 text-xs font-semibold text-slate-300">{student.admission_number}</td>
                        <td className="py-3.5 px-4 text-xs text-slate-400">{student.class_or_department || 'General'}</td>
                        <td className="py-3.5 px-4 text-xs text-slate-400">{student.email}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => handleDeleteStudent(student.user_id)}
                            className="bg-rose-600/10 hover:bg-rose-600/25 border border-rose-600/20 text-rose-455 font-bold text-[10px] px-3 py-1.5 rounded-lg uppercase transition"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                    {allStudents.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500 text-xs">
                          No active students found in directory.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
