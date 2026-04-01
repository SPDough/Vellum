'use client';

import React, { Suspense } from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import SearchPage from '@/components/pages/SearchPage';

function SearchPageContent() {
  return (
    <NextLayout>
      <SearchPage />
    </NextLayout>
  );
}

export default function SearchRoutePage() {
  return (
    <Suspense fallback={null}>
      <SearchPageContent />
    </Suspense>
  );
}
