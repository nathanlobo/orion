import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Orion Command Center',
  description: 'ROS 2 Orion Robotics Control Dashboard',
  icons: { icon: 'data:,' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}