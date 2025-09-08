'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  PlusIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

const sidebarItems = [
  { name: '새 덱 생성', href: '/', icon: PlusIcon, color: 'text-orange-500' },
  { name: '덱 목록', href: '/decks', icon: DocumentTextIcon },
  { name: '설정', href: '/settings', icon: Cog6ToothIcon }
];

interface RecentDeck {
  deck_id: string;
  title: string;
  status: string;
}

export default function Sidebar() {
  const pathname = usePathname();
  const [recentDecks, setRecentDecks] = useState<RecentDeck[]>([]);

  useEffect(() => {
    fetchRecentDecks();
  }, []);

  const fetchRecentDecks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/decks?limit=3');
      if (response.ok) {
        const decks = await response.json();
        setRecentDecks(decks);
      }
    } catch (error) {
      console.error('Error fetching recent decks:', error);
    }
  };

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-white rounded"></div>
          <span className="font-semibold">Deckflow</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <item.icon className={`w-5 h-5 ${item.color || 'text-current'}`} />
              {item.name}
            </Link>
          );
        })}

        {/* Projects Section */}
        <div className="pt-6">
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              최근 항목
            </span>
          </div>
          <div className="space-y-1">
            {recentDecks.map((deck) => (
              <Link
                key={deck.deck_id}
                href={deck.status === 'completed' ? `/decks/${deck.deck_id}/preview` : `/decks`}
                className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white rounded-lg transition-colors"
              >
                <div className="w-5 h-5 flex-shrink-0">
                  {deck.status === 'generating' ? (
                    <div className="w-3 h-3 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
                  ) : deck.status === 'completed' ? (
                    <DocumentTextIcon className="w-4 h-4" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4" />
                  )}
                </div>
                <span className="truncate" title={deck.title}>{deck.title}</span>
              </Link>
            ))}
            {recentDecks.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-500">
                아직 생성된 덱이 없습니다
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium">SK</span>
          </div>
          <div>
            <div className="text-sm font-medium">SUNHO KIM</div>
            <div className="text-xs text-gray-400">Pro 요금제</div>
          </div>
        </div>
      </div>
    </div>
  );
}
