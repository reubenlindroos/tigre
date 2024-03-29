from __future__ import division
import numpy as np
#TODO: Implement angularDistance (for blocks)

def order_subsets(angles, blocksize, mode):
    # Parse no blocks
    if blocksize==1 or blocksize==None:
        index_alpha=np.arange(len(angles))

        if mode =='ordered' or mode==None:
            return angles, index_alpha

        if mode =='random':
            np.random.shuffle(index_alpha)
            return angles[index_alpha], index_alpha
        if mode == 'angularDistance':
            # Sort values according to size
            index_alpha=np.argsort(angles)
            # Save the first values for index_alpha and angles in the new lists
            # (this needs to be done or argmin will return error otherwise)
            new_index = [index_alpha[0]]
            new_angles = [angles[index_alpha[0]]]
            # remove the first values from the original arrays
            angles = np.delete(angles[index_alpha],0)
            index_alpha=np.delete(index_alpha,0)
            # Run through list
            for i in range(len(angles)):
                # Run the comparison
                compangle = new_angles[i]
                angles_min = np.argmin(abs(abs(angles-compangle)-(np.pi/2)))
                # Save the results to the new lists
                new_angles.append(angles[angles_min])
                new_index.append(index_alpha[angles_min])
                # delete old values from the original arrays
                angles=np.delete(angles,angles_min)
                index_alpha=np.delete(index_alpha,angles_min)

            print(len(new_angles),len(new_index))
            return np.array(new_angles,dtype=np.float32), new_index


        else:
            raise NameError('OrdStrat string not recognised: ' + mode)

    # Parse with blocks
    elif blocksize>1:
        # using list comprehension to form the blocks.
        oldindex=np.arange(len(angles))
        index_alpha = [oldindex[i:i+blocksize] for i in range(0,len(oldindex),blocksize)]
        block_alpha = [angles[i:i+blocksize] for i in range(0,len(angles),blocksize)]
        if mode == 'ordered' or mode==None:
            return block_alpha, index_alpha

        if mode == 'random':
            new_order=np.random.shuffle(np.arange(len(index_alpha)))
            return block_alpha[new_order],index_alpha[new_order]
        if mode =='angularDistance':
            # TODO: implement this.
            raise NameError('Angular distance not implemented for blocksize >1 (yet!)')

        else:
            raise NameError('OrdStrat string not recognised: ' + mode)

