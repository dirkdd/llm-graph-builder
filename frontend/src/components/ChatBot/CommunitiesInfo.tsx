import { LoadingSpinner, Flex, Typography, TextLink } from '@neo4j-ndl/react';
import { FC, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { CommunitiesProps } from '../../types';
import { chatModeLables } from '../../utils/Constants';
import GraphViewModal from '../Graph/GraphViewModal';
import { handleGraphNodeClick } from './chatInfo';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
const CommunitiesInfo: FC<CommunitiesProps> = ({ loading, communities, mode }) => {
  const [neoNodes, setNeoNodes] = useState<any[]>([]);
  const [neoRels, setNeoRels] = useState<any[]>([]);
  const [openGraphView, setOpenGraphView] = useState(false);
  const [viewPoint, setViewPoint] = useState('');
  const [loadingGraphView, setLoadingGraphView] = useState(false);

  const handleCommunityClick = (elementId: string, viewMode: string) => {
    handleGraphNodeClick(
      elementId,
      viewMode,
      setNeoNodes,
      setNeoRels,
      setOpenGraphView,
      setViewPoint,
      setLoadingGraphView
    );
  };

  return (
    <>
      {loading ? (
        <div className='flex justify-center items-center'>
          <LoadingSpinner size='small' />
        </div>
      ) : communities?.length > 0 ? (
        <div className='p-4 h-80 overflow-auto'>
          <ul className='list-none list-inside'>
            {communities.map((community, index) => (
              <li key={`${community.id}${index}`} className='mb-2'>
                <div>
                  <Flex flexDirection='row' gap='2'>
                    <TextLink
                      className={`${loadingGraphView ? 'cursor-wait' : 'cursor-pointer'}`}
                      htmlAttributes={{
                        onClick: () => handleCommunityClick(community.element_id, 'chatInfoView'),
                      }}
                    >{`ID : ${community.id}`}</TextLink>
                  </Flex>
                  {mode === chatModeLables['global search+vector+fulltext'] && community.score && (
                    <Flex flexDirection='row' gap='2'>
                      <Typography variant='subheading-medium'>Score : </Typography>
                      <Typography variant='subheading-medium'>{community.score}</Typography>
                    </Flex>
                  )}
                  <div className='prose prose-sm sm:prose lg:prose-lg xl:prose-xl max-w-none'>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw] as any}>
                      {community.summary}
                    </ReactMarkdown>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <Typography variant='h6' className='text-center'>
          {' '}
          No Communities Found
        </Typography>
      )}
      {openGraphView && (
        <GraphViewModal
          open={openGraphView}
          setGraphViewOpen={setOpenGraphView}
          viewPoint={viewPoint}
          nodeValues={neoNodes}
          relationshipValues={neoRels}
        />
      )}
    </>
  );
};

export default CommunitiesInfo;
