declare module 'react-window' {
  import * as React from 'react';

  export interface ListChildComponentProps {
    index: number;
    style: React.CSSProperties;
    data?: any;
    isScrolling?: boolean;
  }

  export interface ListProps {
    height: number;
    itemCount: number;
    itemSize: number;
    width: number | string;
    children: React.ComponentType<ListChildComponentProps>;
    className?: string;
    style?: React.CSSProperties;
    overscanCount?: number;
  }

  export class List extends React.Component<ListProps> {}
}
