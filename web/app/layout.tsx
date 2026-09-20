import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Humanoid Command Center',
  description: 'ROS 2 Humanoid Robotics Control Dashboard',
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