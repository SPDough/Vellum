'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import Transactions from '@/components/pages/Transactions';

export default function TransactionsPage() {
  return (
    <NextLayout>
      <Transactions />
    </NextLayout>
  );
}